"""One playback/serial worker; the GUI only reads coalesced snapshots."""
from collections import deque
from dataclasses import dataclass, replace
import threading
import time
from types import MappingProxyType

from arrangement_model import PPQ
from arrangement_playback import ArrangementPlayer, Plan


@dataclass(frozen=True)
class PlaybackSnapshot:
    state: str = 'stopped'
    message: str = '后台调度就绪：离线编排不发送串口'
    plan: object = None
    position: float = 0.0
    active: object = None
    last_event: object = None
    loop: bool = False
    max_lateness: float = 0.0
    max_write_seconds: float = 0.0
    last_error: str = ''
    controls: tuple = ()
    controls_version: int = 0
    published_at: float = 0.0
    preparing: bool = False

    @property
    def tick(self):
        return 0 if self.plan is None else self.plan.start_tick + round(self.position * self.plan.bpm * PPQ / 60)


class ThreadedArrangementPlayer:
    def __init__(self, send=None, clock=time.monotonic):
        self._condition = threading.Condition()
        self._requests = deque()
        self._interrupt = threading.Event()
        self._thread = None
        self._closing = False
        self._requested_revision = self._completed_revision = self._executing_revision = 0
        self._timer = None
        self._timer_id = 0
        self._sender = self._default_sender = send
        self._failed_transport = None
        self._controls = {}
        self._controls_version = 0
        self._snapshot = PlaybackSnapshot(active=MappingProxyType({}))
        self._core = ArrangementPlayer(self._send, self._schedule, self._cancel, self._publish,
                                       clock=clock, batch_simultaneous=True,
                                       interrupted=self._interrupt.is_set)

    def snapshot(self):
        with self._condition:
            return self._snapshot

    def __getattr__(self, name):
        if name in PlaybackSnapshot.__dataclass_fields__ or name == 'tick':
            return getattr(self.snapshot(), name)
        raise AttributeError(name)

    @property
    def _job(self):
        # No Tk callback is used to schedule playback.
        return None

    def _enqueue(self, kind, payload, snapshot):
        with self._condition:
            if self._closing:
                return False
            self._requested_revision += 1
            self._requests.append((self._requested_revision, kind, payload))
            self._snapshot = snapshot
            self._interrupt.set()
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name='ArrangementPlayback', daemon=True)
                self._thread.start()
            self._condition.notify_all()
            return True

    def play(self, plan, loop=False, send=None):
        if not isinstance(plan, Plan):
            raise ValueError('无效播放计划')
        return self._enqueue('play', (plan, loop, send if send is not None else self._default_sender),
                             replace(self.snapshot(), state='playing', message='准备后台播放', plan=plan,
                                     position=0, active=MappingProxyType({}), last_event=None, loop=loop,
                                     max_lateness=0, max_write_seconds=0, last_error='', published_at=0., preparing=True))

    def stop(self, message='已停止；鼓与空间效果可能保留自然尾音'):
        return self._enqueue('stop', message, replace(self.snapshot(), state='stopped',
                                                     message=message + '（正在清理声部）'))

    def wait_ready(self, timeout=0.4):
        """For disconnect/close and tests, never the normal GUI play callback."""
        deadline = time.monotonic() + timeout
        with self._condition:
            revision = self._requested_revision
            while self._completed_revision < revision:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True

    def shutdown(self, timeout=0.4):
        with self._condition:
            if not self._closing:
                self._closing = True
                self._interrupt.set()
                self._requested_revision += 1
                self._requests.append((self._requested_revision, 'shutdown', None))
                self._condition.notify_all()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)
        return thread is None or not thread.is_alive()

    def _schedule(self, milliseconds, callback):
        with self._condition:
            self._timer_id += 1
            self._timer = (self._timer_id, time.monotonic() + milliseconds / 1000, callback)
            self._condition.notify_all()
            return self._timer_id

    def _cancel(self, token):
        with self._condition:
            if self._timer is not None and self._timer[0] == token:
                self._timer = None

    def _publish(self, core):
        snapshot = PlaybackSnapshot(core.state, core.message, core.plan, core.position,
                                    MappingProxyType(dict(core.active)), core.last_event, core.loop,
                                    core.max_lateness, core.max_write_seconds, core.last_error,
                                    tuple(self._controls.values()), self._controls_version,
                                    time.monotonic(), core._preparing)
        with self._condition:
            if self._executing_revision == self._requested_revision:
                self._snapshot = snapshot

    def _send(self, data):
        sender = self._sender
        try:
            if sender is None or not sender(data):
                raise IOError('播放发送接口不可用或返回失败')
        except Exception:
            self._failed_transport = getattr(sender, 'port', sender)
            raise
        if len(data) % 6:
            return True  # Envelope data packets are 38 bytes, not control frames.
        for offset in range(0, len(data), 6):
            frame = data[offset:offset + 6]
            if len(frame) == 6 and frame[0] == 0xa5 and frame[1] in (3, 4, 0x13, 0x70):
                key = (frame[1], frame[2] if frame[1] == 0x70 else 0)
                self._controls[key] = frame
                self._controls_version += 1
        return True

    def _handle(self, kind, payload):
        core = self._core
        if kind in ('stop', 'shutdown'):
            if core.state != 'stopped':
                core.stop(payload or '关闭编曲工作台')
            elif not core.last_error:
                core.message = payload or '关闭编曲工作台'
            self._publish(core)
            return
        plan, loop, sender = payload
        if core.state != 'stopped' and not core.stop('重新播放前清声'):
            return
        transport = getattr(sender, 'port', sender)
        if plan.hardware and transport is not None and transport is self._failed_transport:
            core.state = 'stopped'
            core.message = '本次连接发生过串口发送故障；请断开重连后再播放，板端状态未知'
            self._publish(core)
            return
        # Each plan retains its own connection even if the GUI later reconnects.
        self._sender = sender
        core.play(plan, loop)
        self._publish(core)

    def _run(self):
        while True:
            with self._condition:
                while not self._requests:
                    if self._timer is None:
                        self._condition.wait()
                    else:
                        remaining = self._timer[1] - time.monotonic()
                        if remaining > 0:
                            self._condition.wait(remaining)
                        else:
                            break
                request = self._requests.popleft() if self._requests else None
                callback = None
                if request:
                    revision, kind, payload = request
                    self._executing_revision = revision
                    stale = kind == 'play' and revision != self._requested_revision
                    if not self._requests:
                        self._interrupt.clear()
                else:
                    revision, kind, payload, stale = self._executing_revision, 'tick', None, False
                    callback = self._timer[2]
                    self._timer = None
            try:
                if not stale:
                    if callback:
                        callback()
                    else:
                        self._handle(kind, payload)
            except Exception as error:
                self._core.last_error = str(error)
                self._core.stop('后台播放异常：' + str(error))
                self._publish(self._core)
            finally:
                if request:
                    with self._condition:
                        self._completed_revision = max(self._completed_revision, revision)
                        self._condition.notify_all()
            if kind == 'shutdown':
                return
