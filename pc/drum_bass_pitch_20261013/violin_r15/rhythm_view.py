"""Native Canvas approach circles, curved sliders, judgement bursts and trails."""
import math
import random
import tkinter as tk


BG = '#0B1121'
PALETTE = ('#5AE0CF', '#8C9DFF', '#F7B46C', '#F18CC5')


def blend(first, second, amount):
    a, b = first.lstrip('#'), second.lstrip('#')
    t = max(0., min(1., amount))
    return '#' + ''.join(f'{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02x}' for i in (0, 2, 4))


class RhythmView(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, background=BG, highlightthickness=0, height=510, takefocus=True)
        self.objects, self.bursts = {}, []
        self.pointer = None
        self.trail = []
        self.scale, self.ox, self.oy = 1000., 0., 0.
        self._size = None
        self.last_wall = None
        self.fps = 0.
        randomizer = random.Random(138)
        self.stars = [(randomizer.random(), randomizer.random(), randomizer.uniform(.2, 1)) for _ in range(34)]
        self.bind('<Configure>', self._resize)
        self._make_background()

    def point(self, x, y):
        return self.ox+x*self.scale, self.oy+y*self.scale

    def world(self, x, y):
        return (x-self.ox)/self.scale, (y-self.oy)/self.scale

    def _oval(self, item, x, y, radius):
        px, py = self.point(x, y)
        r = radius*self.scale
        self.coords(item, px-r, py-r, px+r, py+r)

    def _resize(self, event=None):
        width, height = max(100, self.winfo_width()), max(100, self.winfo_height())
        self.scale = min(width, height/.65)
        self.ox, self.oy = (width-self.scale)/2, (height-.65*self.scale)/2
        if self._size != (width, height):
            self._size = width, height
            self._make_background()

    def _make_background(self):
        self.delete('background')
        width, height = self._size or (1100, 550)
        for i in range(16):
            self.create_rectangle(0, height*i/16, width, height*(i+1)/16, width=0,
                fill=blend('#121B35', BG, i/15), tags='background')
        self.star_items = [self.create_oval(0, 0, 2, 2, fill='#334464', width=0, tags='background') for _ in self.stars]
        self.beat_ring = self.create_oval(0, 0, 1, 1, outline='#1B2A44', width=2, tags='background')
        self.create_text(width-28, height-25, text='XINZOUJIE / FPGA MUSIC', anchor='e',
                         fill='#263956', font=('Segoe UI', 11, 'bold'), tags='background')
        self.lower('background')

    def reset(self):
        self.delete('target')
        self.delete('burst')
        self.delete('trail')
        self.objects.clear()
        self.bursts.clear()
        self.trail.clear()
        self.last_wall = None

    def burst(self, judgement, wall):
        self.bursts.append((judgement, wall))
        self.bursts = self.bursts[-16:]

    def _target_items(self, target, color):
        path = self.create_line(0, 0, 1, 1, fill=blend(color, BG, .83), width=24,
                                capstyle='round', smooth=True, tags='target')
        center = self.create_line(0, 0, 1, 1, fill=blend(color, BG, .50), width=2, smooth=True, tags='target')
        glow = self.create_oval(0, 0, 1, 1, fill='', outline=blend(color, BG, .72), width=9, tags='target')
        disc = self.create_oval(0, 0, 1, 1, fill=blend(color, BG, .87), outline=color, width=3, tags='target')
        ring = self.create_oval(0, 0, 1, 1, outline=color, width=2, tags='target')
        number = self.create_text(0, 0, text=str(target.id%8+1), fill='#F4F8FF',
                                  font=('Segoe UI', 19, 'bold'), tags='target')
        label = self.create_text(0, 0, text=target.label, fill='#A9BCD5', font=('Microsoft YaHei UI', 9), tags='target')
        ball = self.create_oval(0, 0, 1, 1, fill='#FFFFFF', outline=color, width=4, tags='target')
        return path, center, glow, disc, ring, number, label, ball

    def draw(self, chart, session, song_time, wall, pointer=None, mode='', summary=None, preparing=False):
        self._resize()
        width, height = self._size or (1100, 550)
        if self.last_wall is not None and wall > self.last_wall:
            self.fps = self.fps*.94 + (1/(wall-self.last_wall))*.06
        self.last_wall = wall
        for (x, y, weight), item in zip(self.stars, self.star_items):
            px, py = (x*width+wall*weight*3)%width, (y*height+math.sin(wall*.25+x*8)*5)
            self.coords(item, px, py, px+weight*2, py+weight*2)
        phase = (max(0., song_time)*chart.bpm/60) % 1
        beat_radius = .25 + phase*.07
        self._oval(self.beat_ring, .5, .325, beat_radius)
        self.itemconfigure(self.beat_ring, outline=blend('#345072', BG, .40+phase*.5))
        visible = session.visible(song_time) if session else chart.targets[:3]
        shown = [target for target in visible if session is None or target.id not in session.done]
        wanted = {target.id for target in shown}
        for identifier in list(self.objects):
            if identifier not in wanted:
                for item in self.objects.pop(identifier):
                    self.delete(item)
        radius = chart.radius
        self.delete('guide')
        for first, second in zip(shown, shown[1:]):
            self.create_line(*self.point(first.x, first.y), *self.point(second.x, second.y),
                fill='#253550', width=1, dash=(3, 9), tags='guide')
        self.lower('guide')
        self.lower('background')
        for target in reversed(shown):
            color = PALETTE[(target.id//8)%len(PALETTE)]
            items = self.objects.setdefault(target.id, self._target_items(target, color)) if target.id not in self.objects else self.objects[target.id]
            path, center, glow, disc, ring, number, label, ball = items
            early = max(0., min(1., (target.at-song_time)/chart.approach))
            opacity = min(1., (1-early)*5)
            color = blend(BG, color, opacity)
            self._oval(glow, target.x, target.y, radius*1.06)
            self._oval(disc, target.x, target.y, radius)
            self._oval(ring, target.x, target.y, radius*(1+2.8*early))
            self.itemconfigure(disc, outline=color)
            self.itemconfigure(ring, outline=color, state='normal' if target.at>=song_time else 'hidden')
            self.coords(number, *self.point(target.x, target.y))
            self.coords(label, *self.point(target.x, target.y+radius+.020))
            if target.slider:
                points = [v for i in range(25) for v in self.point(*target.position(i/24))]
                self.coords(path, *points)
                self.coords(center, *points)
                self.itemconfigure(path, state='normal', width=max(10, radius*self.scale*1.40))
                self.itemconfigure(center, state='normal')
                progress = max(0., min(1., (song_time-target.at)/target.duration))
                self._oval(ball, *target.position(progress), radius*.46)
                self.itemconfigure(ball, state='normal' if song_time >= target.at else 'hidden')
            else:
                for item in (path, center, ball):
                    self.itemconfigure(item, state='hidden')
        self.delete('trail')
        if pointer is not None:
            self.trail.append((pointer, wall))
        self.trail = [(point, born) for point, born in self.trail if wall-born < .16][-14:]
        for point, born in self.trail:
            age = (wall-born)/.16
            x, y = self.point(*point)
            r = (1-age)*7+2
            self.create_oval(x-r, y-r, x+r, y+r, fill=blend('#F8DB99', BG, age), width=0, tags='trail')
        if pointer is not None:
            x, y = self.point(*pointer)
            self.create_oval(x-11, y-11, x+11, y+11, outline='#FFE4AE', width=2, tags='trail')
        self.delete('burst')
        self.bursts = [(judgement, born) for judgement, born in self.bursts if wall-born < .65]
        for judgement, born in self.bursts:
            age = (wall-born)/.65
            color = '#FF7392' if judgement.score == 0 else '#76F0D7' if judgement.score == 300 else '#FFD08D'
            color = blend(color, BG, age)
            x, y = self.point(judgement.target.x, judgement.target.y)
            r = radius*self.scale*(1+age*1.5)
            self.create_oval(x-r, y-r, x+r, y+r, outline=color, width=max(1, 4*(1-age)), tags='burst')
            for i in range(10):
                angle = i*math.tau/10
                px, py = x+math.cos(angle)*r*1.15, y+math.sin(angle)*r*1.15
                rr = max(1, 3*(1-age))
                self.create_oval(px-rr, py-rr, px+rr, py+rr, fill=color, width=0, tags='burst')
            self.create_text(x, y-35-age*38, text=judgement.text, fill=color,
                             font=('Segoe UI', 16, 'bold'), tags='burst')
        self.delete('hud')
        combo = session.combo if session else 0
        score = session.score if session else 0
        accuracy = session.accuracy if session else 100.
        self.create_text(26, 24, text=f'{score:08d}', fill='#F1F6FF', anchor='nw',
                         font=('Segoe UI', 27, 'bold'), tags='hud')
        self.create_text(width-26, 27, text=f'{accuracy:06.2f}%', fill='#67DFCD', anchor='ne',
                         font=('Segoe UI', 24, 'bold'), tags='hud')
        self.create_text(28, height-23, text=f'{combo}x', fill='#EEF5FF', anchor='sw',
                         font=('Segoe UI', 31, 'bold'), tags='hud')
        self.create_text(30, 70, text=mode, fill='#93A6C6', anchor='nw', font=('Microsoft YaHei UI', 9), tags='hud')
        hp = session.hp if session else 100
        self.create_rectangle(width-205, 64, width-27, 69, fill='#26354E', width=0, tags='hud')
        self.create_rectangle(width-205, 64, width-205+178*hp/100, 69, fill='#69D4BD', width=0, tags='hud')
        progress = max(0., min(1., song_time/chart.duration))
        self.create_rectangle(0, height-4, width*progress, height, fill='#8D98F7', width=0, tags='hud')
        self.create_text(width-28, height-45, text=f'{max(0,int(song_time))} / {int(chart.duration)}s · {self.fps:.0f} FPS',
                         fill='#7286A7', anchor='se', font=('Segoe UI', 9), tags='hud')
        if session and session.recent:
            y = height-30
            self.create_line(width/2-75, y, width/2+75, y, fill='#41516B', width=3, tags='hud')
            self.create_line(width/2, y-6, width/2, y+6, fill='#B6C7DA', tags='hud')
            for judgement in session.recent[-24:]:
                if judgement.score:
                    x = width/2+max(-75,min(75,judgement.error_ms/160*75))
                    self.create_line(x,y-5,x,y+5,fill='#73E3D0',tags='hud')
        if preparing or song_time < -.05:
            text = '准备音色…' if preparing else str(max(1, math.ceil(-song_time)))
            self.create_text(width/2, height/2, text=text, fill='#F0F5FF', font=('Microsoft YaHei UI', 51, 'bold'), tags='hud')
        if summary is not None:
            self.create_rectangle(width*.19,height*.15,width*.81,height*.84,fill='#142039',outline='#60709E',width=2,tags='hud')
            grade = 'S' if summary['accuracy']>=95 else 'A' if summary['accuracy']>=85 else 'B' if summary['accuracy']>=70 else 'C'
            self.create_text(width/2,height*.29,text='DEMO' if summary['autoplay'] else grade,
                fill='#7CE4D2',font=('Segoe UI',46,'bold'),tags='hud')
            self.create_text(width/2,height*.47,text=f"{summary['score']:08d}  /  {summary['accuracy']:.2f}%",fill='#F1F5FF',font=('Segoe UI',23,'bold'),tags='hud')
            counts=summary['counts']
            detail='  ·  '.join(f'{name} {counts.get(name,0)}' for name in ('PERFECT','GOOD','OK','MISS'))
            self.create_text(width/2,height*.60,text=detail,fill='#AFC1DD',font=('Segoe UI',11),tags='hud')
            self.create_text(width/2,height*.71,text=f"MAX COMBO {summary['max_combo']}x  ·  {'演示不记录成绩' if summary['autoplay'] else '点击重新挑战继续'}",fill='#90A6C6',font=('Microsoft YaHei UI',11),tags='hud')
