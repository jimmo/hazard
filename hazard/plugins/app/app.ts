import { Surface, Form, Button, Label, CoordAxis, Tree, TreeNode, SimpleTreeNode, ButtonGroup, SimpleTreeLeafNode, Dialog, TextBox, AlertDialog, Box } from 'canvas-forms';
import { ZigBeeTree } from './zigbee';

const form = new Form(new Surface('canvas'));

const title = form.add(new Label('Hazard'), { y: 0 });
title.fit = true;
title.coords.center(CoordAxis.X);


const tabs = form.add(new ButtonGroup(), { x: 10, h: 28, x2: 10, y2: 6 });
const mapButton = tabs.add(new Button('Map'));
const groupsButton = tabs.add(new Button('Groups'));
const actionsButton = tabs.add(new Button('Actions'));
const zigbeeButton = tabs.add(new Button('ZigBee'));

const container = form.add(new Box(), { x: 0, y: 30, x2: 0 });
container.coords.yh.align(tabs.coords.y, -4);


zigbeeButton.click.add(() => {
  container.clear();
  const zigbeeTree = container.add(new ZigBeeTree(), 0, 0, null, null, 0, 0);
});
