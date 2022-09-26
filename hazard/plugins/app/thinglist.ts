import { List, ClickableListItem, ListItem, Label, AlertDialog, Dialog, CoordAxis, Button, ButtonGroup, Ionicons, Slider, SliderDirection, FontStyle, StyleColor, FocusTextBox, Control, TextBox, TextAlign, MenuItems, MenuItem, PromptDialog } from "canvas-forms";
import { Thing, Switch, Light, SwitchButton, Clock, Temperature, DoorSensor, MotionSensor } from "./hazard";
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

        const group = this.add(new ButtonGroup(), { x: 30, y: 10, x2: 30, h: 60 });
        const on = group.add(new Button('On', Ionicons.RadioButtonOn));
        const off = group.add(new Button('Off', Ionicons.RadioButtonOff));
        const toggle = group.add(new Button('Toggle', Ionicons.Toggle));

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

        this.add(new Label('Level'), 30, 10, 100, 50);
        const slider = this.add(new LevelSlider(thing.level, 0, 7, 1), { x: 100, y: 10, x2: 30, h: 50 });
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

        this.add(new Label('Temp'), 30, 10, 100, 50);
        const slider = this.add(new TemperatureSlider(thing.temperature, 0, 7, 1), { x: 100, y: 10, x2: 30, h: 50 });
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

        this.add(new Label('Colour'), 30, 10, 100, 50);
        const slider = this.add(new Slider(thing.hue, 0, 1, 0.01), { x: 100, y: 10, x2: 30, h: 50 });
        slider.change.add(() => {
            thing.action('hue', {
                hue: slider.value,
            });
        }, 500);
    }
}

class ThingActionSaturation extends ThingAction {
    constructor(thing: Light) {
        super(thing);

        this.add(new Label('Satn'), 30, 10, 100, 50);
        const slider = this.add(new Slider(thing.saturation, 0, 1, 0.1), { x: 100, y: 10, x2: 30, h: 50 });
        slider.change.add(() => {
            thing.action('saturation', {
                saturation: slider.value,
            });
        }, 500);
    }
}

class ThingActionSwitchButtonCodeDialog extends Dialog {
    constructor(readonly thing: Switch, readonly button: SwitchButton) {
        super();

        let l = this.add(new Label('Single'), 10, 10);
        l.fit = true;
        const single = this.add(new TextBox(button.single), { x: 10, y: 40, x2: 10, h: 100 });
        single.fontName = 'monospace';
        single.multiline = true;

        l = this.add(new Label('Double'), 10, 10 + 140);
        l.fit = true;
        const double = this.add(new TextBox(button.double), { x: 10, y: 40 + 140, x2: 10, h: 100 });
        double.fontName = 'monospace';
        double.multiline = true;

        let n = 2;
        let tap: TextBox = null;
        if (thing.hasFeature("switch-tap")) {
            l = this.add(new Label('Tap'), 10, 10 + 140 * 2);
            l.fit = true;
            tap = this.add(new TextBox(button.tap), { x: 10, y: 40 + 140 * 2, x2: 10, h: 100 });
            tap.fontName = 'monospace';
            tap.multiline = true;
            n += 1;
        }

        let hold: TextBox = null;
        if (thing.hasFeature("switch-hold")) {
            l = this.add(new Label('Hold'), 10, 10 + 140 * n);
            l.fit = true;
            hold = this.add(new TextBox(button.hold), { x: 10, y: 40 + 140 * n, x2: 10, h: 100 });
            hold.fontName = 'monospace';
            hold.multiline = true;
        }

        this.add(new Button('Cancel'), { x2: 20, y2: 20 }).click.add(() => {
            this.close(null);
        });
        this.add(new Button('OK'), { x2: 230, y2: 20 }).click.add(() => {
            this.button.single = single.text;
            this.button.double = double.text;
            if (thing.hasFeature("switch-tap")) {
                this.button.tap = tap.text;
            }
            if (thing.hasFeature("switch-hold")) {
                this.button.hold = hold.text;
            }
            this.thing.save();
            this.close(null);
        });
    }

    defaultConstraints() {
        // Override Dialog default which centers a fixed width/height dialog in the form.
        this.coords.x.set(20);
        this.coords.x2.set(20);
        this.coords.h.set(650)
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

class ThingActionMotionSensor extends ThingAction {
    constructor(thing: MotionSensor) {
        super(thing);
    }
}

class ThingActionDoorSensor extends ThingAction {
    constructor(thing: DoorSensor) {
        super(thing);
    }
}

class ThingActionClock extends ThingAction {
    constructor(thing: Clock) {
        super(thing);

        let l = this.add(new Label('Interval (s)'), 20, 20, 160);
        const interval = this.add(new TextBox(thing.interval.toString()), 180, 20, 200);

        l = this.add(new Label('Code'), 20, 70, 100);
        const code = this.add(new TextBox(thing.code), 20, 110, null, 360, 20);
        code.multiline = true;
        code.fontName = 'monospace';

        code.change.add(() => {
            thing.code = code.text;
            thing.save();
        }, 1000);

        interval.change.add(() => {
            thing.interval = parseInt(interval.text, 10);
            thing.save();
        });
    }
}

class ThingActionTemperature extends ThingAction {
    constructor(thing: Temperature) {
        super(thing);

        this.add(new Label('Temperature'), 20, 20, 160);
        if (thing.temperature !== null) {
            this.add(new Label(thing.displayTemperature), 180, 20, 200);
        }
    }
}

class ThingActionHumidity extends ThingAction {
    constructor(thing: Temperature) {
        super(thing);

        this.add(new Label('Humidity'), 20, 20, 160);
        if (thing.humidity !== null) {
            this.add(new Label(thing.displayHumidity), 180, 20, 200);
        }
    }
}

class ThingActionLastUpdated extends ThingAction {
    constructor(thing: Temperature) {
        super(thing);

        this.add(new Label('Last updated'), 20, 20, 160);
        this.add(new Label(thing.displayLastUpdated), 180, 20, 200);
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
        if (thing.hasFeature('light-saturation')) {
            list.addItem(thing as Light, ThingActionSaturation);
        }
        if (thing.hasFeature('switch')) {
            list.addItem(thing as Switch, ThingActionSwitch);
        }
        if (thing.hasFeature('clock')) {
            list.addItem(thing as Clock, ThingActionClock);
        }
        if (thing.hasFeature('temperature')) {
            list.addItem(thing as Temperature, ThingActionTemperature);
        }
        if (thing.hasFeature('humidity')) {
            list.addItem(thing as Temperature, ThingActionHumidity);
        }
        if (thing.hasFeature('temperature')) {
            list.addItem(thing as Temperature, ThingActionLastUpdated);
        }
        if (thing.hasFeature('motion')) {
            list.addItem(thing as Temperature, ThingActionMotionSensor);
        }
        if (thing.hasFeature('door')) {
            list.addItem(thing as Temperature, ThingActionDoorSensor);
        }

        const close = this.add(new Button('Close'), { y2: 20, w: 160 });
        close.coords.center(CoordAxis.X);
        close.click.add(() => {
            this.close();
        });

        const reconfigure = this.add(new Button(null, Ionicons.Settings), { x2: 20, y2: 20, w: 30 });
        reconfigure.click.add(() => {
            thing.reconfigure();
        });

        if (thing.hasFeature('battery') && thing.battery > 0) {
            const batteryIcon = this.add(new Label(), { x: 20, y2: 20, w: 30 });
            batteryIcon.icon = thing.battery < 30 ? Ionicons.BatteryDead : Ionicons.BatteryFull;
            const batteryLabel = this.add(new Label(thing.battery + "%"), { x: 50, y2: 20 });
        }
    }

    defaultConstraints() {
        // Override Dialog default which centers a fixed width/height dialog in the form.
        this.coords.x.set(20);
        this.coords.y.set(20);
        this.coords.x2.set(20);
        this.coords.y2.set(20);
    }
}


class RoundedSlider extends Slider {
    constructor(value?: number, min?: number, max?: number, snap?: number, direction?: SliderDirection) {
        super(value, min, max, snap, direction);
    }

    protected color() : string {
        return 'white';
    }

    protected paint(ctx: CanvasRenderingContext2D) {
        const r = this._direction == SliderDirection.Horizontal ? (this.h - 4) / 2 : (this.w - 4) / 2;
        this._handleWidth = r * 2;

        ctx.fillStyle = this.color();
        ctx.strokeStyle = this.form.style.color.insetLeft;
        ctx.lineWidth = 1;
        ctx.lineJoin = 'round';

        ctx.beginPath();
        ctx.moveTo(r, 0);
        ctx.lineTo(this.w - r, 0);
        ctx.arcTo(this.w, 0, this.w, r, r);
        ctx.lineTo(this.w, this.h - r);
        ctx.arcTo(this.w, this.h, this.w - r, this.h, r);
        ctx.lineTo(r, this.h);
        ctx.arcTo(0, this.h, 0, this.h - r, r);
        ctx.lineTo(0, r);
        ctx.arcTo(0, 0, r, 0, r);
        ctx.fill();
        ctx.stroke();

        ctx.beginPath();
        if (this._direction == SliderDirection.Horizontal) {
            let x = (this.w - this._handleWidth) * (this._value - this._min) / (this._max - this._min);
            ctx.ellipse(x + r, this.h / 2, r, r, 0, 0, 2 * Math.PI);
        } else {
            let y = (this.h - this._handleWidth) * (this._value - this._min) / (this._max - this._min);
            ctx.ellipse(this.w / 2, y + r, r, r, 0, 0, 2 * Math.PI);
        }
        ctx.fill();
        ctx.strokeStyle = this.form.style.color.insetLeft;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

class LevelSlider extends RoundedSlider {
    constructor(value?: number, min?: number, max?: number, snap?: number, direction?: SliderDirection) {
        super(value, min, max, snap, direction);
    }

    protected color() : string {
        return StyleColor.hslmap(0.125, 1, 1, 0.125, 1, 0.5, this._value, this._min, this._max);
    }
}

class TemperatureSlider extends RoundedSlider {
    constructor(value?: number, min?: number, max?: number, snap?: number, direction?: SliderDirection) {
        super(value, min, max, snap, direction);
    }

    protected color() : string {
        return StyleColor.hslmap(0.8, 1, 0.75, 0.125, 1, 0.75, this._value, this._min, this._max);
    }
}

class ThingListItem extends ClickableListItem<Thing> {
    constructor(readonly thing: Thing) {
        super(thing);

        this.border = true;

        if (thing.hasFeature('light')) {
            const slider = this.add(new LevelSlider((thing as Light).level, 0, 7, 1), { x: 260, y: 2, x2: 2, y2: 2 });
            slider.change.add(() => {
                thing.action('level', {
                    level: slider.value,
                });
            }, 500);
        }

        const l = this.add(new Label(thing.name), { x: 64, y: 3, w: 200, y2: 3 });
        l.fontSize = 22;

        const icon = this.add(new Label(), { x: 3, y: 0, w: 60, y2: 0 });
        icon.fontSize = 52;
        icon.align = TextAlign.CENTER;

        if (thing.hasFeature('group')) {
            icon.icon = Ionicons.Expand;
        } else if (thing.hasFeature('light')) {
            icon.icon = Ionicons.Bulb;
        } else if (thing.hasFeature('switch')) {
            icon.icon = Ionicons.Toggle;
        } else if (thing.hasFeature('clock')) {
            icon.icon = Ionicons.Timer;
        } else if (thing.hasFeature('temperature')) {
            icon.icon = Ionicons.Thermometer;
        } else if (thing.hasFeature('motion')) {
            icon.icon = Ionicons.Magnet;
        } else if (thing.hasFeature('door')) {
            icon.icon = Ionicons.Moon;
        }
        if (thing.hasFeature('light')) {
            icon.color = (thing as Light).on ? 'orange' : 'black';
        }

        if (thing.hasFeature('battery') && thing.battery && thing.battery < 30) {
            icon.color = 'red';
        }

        this.click.add(async (ev) => {
            if (ev.x < 60 && thing.hasFeature('light')) {
                await this.thing.action('toggle');
            } else {
                await new ThingDialog(this.thing).modal(this.form);
            }
            (this.parent as ThingList).update();
        });
    }

    protected defaultConstraints() {
        this.coords.h.set(60);
        return true;
    }

    protected paint(ctx: CanvasRenderingContext2D) {
        super.paint(ctx);

        ctx.strokeStyle = this.form.style.color.separator;
        ctx.lineWidth = 1;

        ctx.beginPath();
        ctx.moveTo(60, 2);
        ctx.lineTo(60, this.h - 2);
        ctx.stroke();
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

export class GroupList extends ThingList {
    constructor() {
        super();
    }

    async update() {
        const things = await Thing.load();
        this.clear();
        things.sort(sortBy('zone', 'type', 'name'));
        for (const thing of things) {
            if (!thing.hasFeature('group')) {
                continue;
            }
            const l = this.addItem(thing);
        }
    }
}
