import unittest,time
from types import SimpleNamespace
from panel_sync import decode_panel_line
from host_controller import ViolinController
class Var:
 def __init__(self,v=0):self.v=v
 def get(self):return self.v
 def set(self,v):self.v=v
class PanelSyncTests(unittest.TestCase):
 def values(self):
  v=[0]*32;v[0]=4;v[19]=3;v[20:25]=[70,80,90,100,110];v[25:29]=[1,5,5,25];v[30]=1;return v
 def test_parse_and_reject_bad_status(self):
  v=self.values();line='PANEL,8,3,34,'+','.join(map(str,v))
  self.assertEqual(decode_panel_line(line),(3,34,tuple(v)))
  for bad in ('PANEL,WAIT',line+',1',line.replace('PANEL,8','PANEL,7'),line.replace(',3,34,',',9,34,')):
   self.assertIsNone(decode_panel_line(bad))
  v[18]=97
  self.assertIsNone(decode_panel_line('PANEL,8,0,0,'+','.join(map(str,v))))
 def controller(self):
  return SimpleNamespace(_last_panel_host_write=0,timbre_text=Var(),piano_pedal=Var(),violin_level=Var(),bus_levels=[127]*5)
 def test_apply_five_levels_and_timbre_without_serial_writes(self):
  c=self.controller();ViolinController.apply_panel_state(c,(3,34,self.values()))
  self.assertEqual(c.current_timbre,3);self.assertEqual(c.current_mode,1)
  self.assertEqual(c.bus_levels,[70,80,110,100,90]);self.assertEqual(c.piano_pedal.get(),3)
  self.assertFalse(c._panel_sync_active)
 def test_recent_pc_change_not_overwritten(self):
  c=self.controller();c._last_panel_host_write=time.monotonic()
  ViolinController.apply_panel_state(c,(0,0,self.values()))
  self.assertEqual(c.bus_levels,[127]*5)
 def test_ensemble_readback_preserves_host_timbre_and_reports_multi_engine_mode(self):
  controller=self.controller();controller.current_timbre=2
  values=self.values();values[31]=1
  ViolinController.apply_panel_state(controller,(3,34,values))
  self.assertEqual(controller.current_timbre,2)
  self.assertIn('独立多乐器',controller.timbre_text.get())
