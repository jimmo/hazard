import { List, ListItem, Label, AlertDialog, Dialog, CoordAxis, Button, ButtonGroup, Ionicons, Slider, FontStyle, FocusTextBox, Control } from "canvas-forms";
import { Thing } from "./hazard";
import { sortBy } from "./utils";

class ThingAction extends ListItem<Thing> {
  constructor(thing: Thing) {
    super(thing);
    this.border = true;
  }

  protected defaultConstraints() {
    this.coords.h.fit(10);
  }
}

class ThingActionOnOff extends ThingAction {
  constructor(thing: Thing) {
    super(thing);

    const group = this.add(new ButtonGroup(), { x: 30, y: 10, x2: 30 });
    const on = group.add(new Button('On', Ionicons.RadioButtonOn));
    const off = group.add(new Button('Off', Ionicons.RadioButtonOff));
    const toggle = group.add(new Button('Toggle', Ionicons.Switch));

    on.click.add(() => {
      thing.action('on');
    });
    off.click.add(() => {
      thing.action('off');
    });
    toggle.click.add(() => {
      thing.action('toggle');
    });
  }
}

class ThingActionLightLevel extends ThingAction {
  constructor(thing: Thing) {
    super(thing);

    this.add(new Label('Level'), 30, 10);
    const slider = this.add(new Slider(1, 0, 1, 0.1), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
      thing.action('level', {
        level: slider.value,
      });
    }, 500);
  }
}

class ThingActionColorTemperature extends ThingAction {
  constructor(thing: Thing) {
    super(thing);

    this.add(new Label('Temp'), 30, 10);
    const slider = this.add(new Slider(10000, 1200, 10000, 100), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
      thing.action('temperature', {
        temperature: slider.value,
      });
    }, 500);
  }
}

class ThingActionColor extends ThingAction {
  constructor(thing: Thing) {
    super(thing);

    this.add(new Label('Colour'), 30, 10);
    const slider = this.add(new Slider(1, 0, 1, 0.1), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
    }, 500);
  }
}

class ThingActionSwitch extends ThingAction {
  constructor(thing: Thing) {
    super(thing);

    const group = this.add(new ButtonGroup(), { x: 30, y: 10, x2: 100, h: 28 });

    for (let i = 0; i < thing.buttons.length; ++i) {
      const btn = group.add(new Button((i + 1).toString(), Ionicons.FingerPrint));
      const index = i;
      btn.click.add(() => {
        thing.action('tap', {
          button: index,
        });
      });
    }

    const edit = this.add(new Button('', Ionicons.Build), { x2: 30, y: 10, w: 40 });
    edit.click.add(() => {
      if (this.controls.length > 2) {
        edit.setActive(false);
        while (this.controls.length > 2) {
          this.controls[this.controls.length - 1].remove();
        }
      } else {
        edit.setActive(true);
        let prev: Control = group;
        for (let i = 0; i < thing.buttons.length; ++i) {
          const labelTap = this.add(new Label((i + 1) + ' - Tap'), 30);
          labelTap.fit = true;
          labelTap.coords.y.align(prev.coords.yh, 10);
          const codeTap = this.add(new FocusTextBox(thing.buttons[i].code.tap), 30, null, null, 140, 30);
          codeTap.multiline = true;
          codeTap.setFont('monospace');
          codeTap.coords.y.align(labelTap.coords.yh, 10);
          const labelDbl = this.add(new Label((i + 1) + ' - Double Tap'), 30, null);
          labelDbl.coords.y.align(codeTap.coords.yh, 10);
          labelDbl.fit = true;
          const codeDbl = this.add(new FocusTextBox(thing.buttons[i].code.doubleTap), 30, null, null, 140, 30);
          codeDbl.multiline = true;
          codeDbl.setFont('monospace');
          codeDbl.coords.y.align(labelDbl.coords.yh, 10);
          prev = codeDbl;
        }
      }
    });
  }
}

export class ThingDialog extends Dialog {
  constructor(readonly thing: Thing) {
    super();

    const title = this.add(new Label(thing.name), { x: 0, y: 10, x2: 0 });
    title.center = true;
    title.addStyle(FontStyle.BOLD);

    const list = this.add(new List<Thing>(ThingAction), { x: 0, x2: 0, y: 40, y2: 50 });
    list.border = false;

    if (thing.hasFeature('light')) {
      list.addItem(thing, ThingActionOnOff);
    }
    if (thing.hasFeature('light-level')) {
      list.addItem(thing, ThingActionLightLevel);
    }
    if (thing.hasFeature('light-temperature')) {
      list.addItem(thing, ThingActionColorTemperature);
    }
    if (thing.hasFeature('light-color')) {
      list.addItem(thing, ThingActionColor);
    }
    if (thing.hasFeature('switch')) {
      list.addItem(thing, ThingActionSwitch);
    }

    const close = this.add(new Button('Close'), { y2: 20, w: 100 });
    close.coords.center(CoordAxis.X);
    close.click.add(() => {
      this.close();
    });
  }

  defaultConstraints() {
    // Override Dialog default which centers a fixed width/height dialog in the form.
    this.coords.x.set(20);
    this.coords.y.set(20);
    this.coords.x2.set(20);
    this.coords.y2.set(20);
  }
}

class ThingListItem extends ListItem<Thing> {
  constructor(readonly thing: Thing) {
    super(thing);

    this.border = true;

    const l = this.add(new Label(thing.name), { x: 3, y: 3, x2: 3, y2: 3 });
    l.center = true;

    this.mousedown.add((ev) => {
      ev.capture();
    });
    this.mouseup.add((ev) => {
      if (ev.capture && ev.inside()) {
        new ThingDialog(this.thing).modal(this.form());
      }
    });
  }

  defaultConstraints() {
    this.coords.h.set(40);
    return true;
  }
}

export class ThingList extends List<Thing> {
  constructor() {
    super(ThingListItem);

    this.update();
  }

  async update() {
    this.clear();

    const things = await Thing.load();
    things.sort(sortBy('zone', 'name'));
    for (const thing of things) {
      if (thing.hasFeature('group')) {
        continue;
      }
      const l = this.addItem(thing);
    }
  }
}

export class GroupList extends List<Thing> {
  constructor() {
    super(ThingListItem);

    this.update();
  }

  async update() {
    this.clear();

    const things = await Thing.load();
    things.sort(sortBy('zone', 'name'));
    for (const thing of things) {
      if (!thing.hasFeature('group')) {
        continue;
      }
      const l = this.addItem(thing);
    }
  }
}
