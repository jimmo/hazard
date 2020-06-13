import { Surface, Form, Button, Label, CoordAxis, Tree, TreeNode, SimpleTreeNode, ButtonGroup, SimpleTreeLeafNode, Dialog, TextBox, AlertDialog, Box, Ionicons, FontStyle, Style, StyleFont } from 'canvas-forms';
import { ZigBeeTree } from './zigbee';
import { ActionList } from './actionlist';
import { MapView } from './mapview';
import { ThingList, GroupList } from './thinglist';

class HazardStyleFont extends StyleFont {
  get size() {
    return 22;
  }
}

const form = new Form(new Surface('canvas'));
form.style.font = new HazardStyleFont();

(async () => {
  await Ionicons.load();
  const title = form.add(new Label('1 Wood St', Ionicons.Home), { y: 0 });
  title.style = FontStyle.ITALIC;
  title.fit = true;
  title.coords.center(CoordAxis.X);

  const tabs = form.add(new ButtonGroup(), { x: 0, h: 40, x2: 0, y2: 0 });

  const container = form.add(new Box(), { x: 0, x2: 0 });
  container.coords.y.align(title.coords.yh);
  container.coords.yh.align(tabs.coords.y, 0);

  const tabButtons: Button[] = [];
  function addTab(name: string, icon: string, callback: () => void) {
    const btn = tabs.add(new Button(name));
    tabButtons.push(btn);
    btn.border = false;
    btn.icon = icon;
    btn.click.add(() => {
      for (const otherBtn of tabButtons) {
        if (otherBtn !== btn) {
          otherBtn.active = false;
        }
      }
      btn.active = true;
      container.clear();
      callback();
    });
    if (tabs.controls.length === 1) {
      btn.active = true;
      callback();
    }
    return btn;
  }

  addTab('Actions', Ionicons.Flash, () => {
    const home = container.add(new ActionList(), 0, 0, null, null, 0, 0);
  });
  addTab('Map', Ionicons.Locate, () => {
    const map = container.add(new MapView(), 0, 0, null, null, 0, 0);
  });
  addTab('Things', Ionicons.Bulb, () => {
    const list = container.add(new ThingList(), 0, 0, null, null, 0, 0);
  });
  addTab('Groups', Ionicons.Expand, () => {
    const list = container.add(new GroupList(), 0, 0, null, null, 0, 0);
  });
  addTab('ZigBee', Ionicons.Hammer, () => {
    const zigbeeTree = container.add(new ZigBeeTree(), 0, 0, null, null, 0, 0);
  });
})();
