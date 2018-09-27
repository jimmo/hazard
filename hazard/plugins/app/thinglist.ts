import { List, ListItem, Label, AlertDialog, Dialog, CoordAxis, Button, ButtonGroup, Ionicons, Slider, FontStyle, FocusTextBox, Control, TextBox, TextAlign, MenuItems, MenuItem, PromptDialog } from "canvas-forms";
import { Thing, Switch, Light, SwitchButton } from "./hazard";
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
  constructor(thing: Light) {
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
  constructor(thing: Light) {
    super(thing);

    this.add(new Label('Level'), 30, 10);
    const slider = this.add(new Slider(thing.level, 0, 1, 0.1), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
      thing.action('level', {
        level: slider.value,
      });
    }, 500);
  }
}

class ThingActionColorTemperature extends ThingAction {
  constructor(thing: Light) {
    super(thing);

    this.add(new Label('Temp'), 30, 10);
    const slider = this.add(new Slider(thing.temperature, 1200, 10000, 100), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
      thing.action('temperature', {
        temperature: slider.value,
      });
    }, 500);
  }
}

class ThingActionColor extends ThingAction {
  constructor(thing: Light) {
    super(thing);

    this.add(new Label('Colour'), 30, 10);
    const slider = this.add(new Slider(1, 0, 1, 0.1), { x: 100, y: 10, x2: 30 });
    slider.change.add(() => {
    }, 500);
  }
}

class ThingActionSwitchButtonCodeDialog extends Dialog {
  constructor(readonly thing: Switch, readonly button: SwitchButton) {
    super();

    let l = this.add(new Label('Single'), 10, 10);
    l.fit = true;
    const single = this.add(new TextBox(button.single), { x: 10, y: 40, x2: 10, h: 120 });
    single.fontName = 'monospace';
    single.multiline = true;

    l = this.add(new Label('Double'), 10, 180);
    l.fit = true;
    const double = this.add(new TextBox(button.double), { x: 10, y: 210, x2: 10, h: 120 });
    double.fontName = 'monospace';
    double.multiline = true;

    this.add(new Button('Cancel'), { x2: 20, y2: 20 }).click.add(() => {
      this.close(null);
    });
    this.add(new Button('OK'), { x2: 190, y2: 20 }).click.add(() => {
      this.button.single = single.text;
      this.button.double = double.text;
      this.thing.save();
      this.close(null);
    });
  }

  defaultConstraints() {
    // Override Dialog default which centers a fixed width/height dialog in the form.
    this.coords.x.set(20);
    this.coords.x2.set(20);
    this.coords.h.set(450)
    this.coords.center(CoordAxis.Y);
  }

}

class ThingActionSwitchButton extends Button {
  constructor(readonly thing: Switch, readonly button: SwitchButton) {
    super(button.name, Ionicons.FingerPrint);
    this.click.add(() => {
      thing.action('invoke', {
        code: button.code,
      });
    });
  }

  protected async contextMenu(): Promise<MenuItems> {
    const rename = new MenuItem('Rename');
    rename.click.add(async () => {
      const result = await new PromptDialog('Button name:', this.button.name).modal(this.form);
      if (result) {
        this.button.name = result;
        this.thing.save();
        this.text = result;
      }
    });

    const edit = new MenuItem('Edit code');
    edit.click.add(async () => {
      await new ThingActionSwitchButtonCodeDialog(this.thing, this.button).modal(this.form);
    });

    return [
      rename,
      edit,
    ]
  }
}

class ThingActionSwitch extends ThingAction {
  constructor(thing: Switch) {
    super(thing);

    let prev: Button = null;

    for (const switchButton of thing.buttons) {
      const btn = this.add(new ThingActionSwitchButton(thing, switchButton), { x: 30, x2: 30, h: 100 });
      if (prev) {
        btn.coords.y.align(prev.coords.yh, 10);
      } else {
        btn.coords.y.set(10);
      }
      prev = btn;
    }
  }
}

export class ThingDialog extends Dialog {
  constructor(readonly thing: Thing) {
    super();

    const title = this.add(new FocusTextBox(thing.name), { x: 0, y: 10, x2: 0 });
    title.border = false;
    title.align = TextAlign.CENTER;
    title.addStyle(FontStyle.BOLD);
    title.change.add(async () => {
      this.thing.name = title.text;
      await this.thing.save();
    }, 1000);

    const list = this.add(new List<Thing>(ThingAction), { x: 0, x2: 0, y: 40, y2: 50 });
    list.border = false;

    if (thing.hasFeature('light')) {
      list.addItem(thing as Light, ThingActionOnOff);
    }
    if (thing.hasFeature('light-level')) {
      list.addItem(thing as Light, ThingActionLightLevel);
    }
    if (thing.hasFeature('light-temperature')) {
      list.addItem(thing as Light, ThingActionColorTemperature);
    }
    if (thing.hasFeature('light-color')) {
      list.addItem(thing as Light, ThingActionColor);
    }
    if (thing.hasFeature('switch')) {
      list.addItem(thing as Switch, ThingActionSwitch);
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
    l.align = TextAlign.CENTER;

    this.mousedown.add((ev) => {
      ev.capture();
    });
    this.mouseup.add((ev) => {
      if (ev.capture && ev.inside()) {
        new ThingDialog(this.thing).modal(this.form);
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
    things.sort(sortBy('zone', 'type', 'name'));
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
    things.sort(sortBy('zone', 'type', 'name'));
    for (const thing of things) {
      if (!thing.hasFeature('group')) {
        continue;
      }
      const l = this.addItem(thing);
    }
  }
}
