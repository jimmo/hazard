import { Label, ScrollBox, Control, TextListItem, List, Ionicons, CheckBox, Grabber, CoordAxis, MenuItems, MenuHeadingItem, MenuItem, PromptDialog, MenuSeparatorItem, ConfirmDialog, ListItem, Spacer } from "canvas-forms";
import { Thing, Light } from './hazard';
import { ThingDialog } from "./thinglist";

class MapThing extends Control {
  constructor(readonly thing: Thing) {
    super();

    const l = this.add(new Label(), 0, 0);
    if (thing.hasFeature('group')) {
      l.icon = Ionicons.Expand;
    } else if (thing.hasFeature('light')) {
      l.icon = Ionicons.Bulb;
    } else if (thing.hasFeature('switch')) {
      l.icon = Ionicons.Switch;
    } else {
      l.text = thing.name;
    }

    if (thing.hasFeature('light')) {
      l.color = (thing as Light).on ? 'orange' : 'black';
    }

    l.fontSize = 40;
    l.fit = true;

    this.mousedown.add((ev) => {
      ev.capture();
      ev.cancelBubble();
    });
    this.mouseup.add(async (ev) => {
      if (ev.capture && ev.inside()) {
        const map = this.parent.parent as MapView;
        await new ThingDialog(this.thing).modal(this.form);
        map.update();
      }
    });
  }

  protected async contextMenu(): Promise<MenuItems> {
    const map = this.parent.parent as MapView;
    if (!map.editing) {
      return null;
    } else {
      const items: MenuItems = [
        new MenuHeadingItem(this.thing.name),
        new MenuSeparatorItem(),
        new MenuHeadingItem('Move to:'),
      ];
      for (const zone of map.zones) {
        if (zone === this.thing.zone) {
          continue;
        }
        const zoneItem = new MenuItem(zone);
        zoneItem.click.add(async () => {
          this.thing.zone = zone;
          await this.thing.save();
          map.updateZones();
        });
        items.push(zoneItem);
      }
      const newItem = new MenuItem('New zone...');
      newItem.click.add(async () => {
        const zone = await new PromptDialog('Zone name', '').modal(this.form);
        this.thing.zone = zone;
        await this.thing.save();
        map.updateZones();
      });
      items.push(newItem);

      items.push(new MenuSeparatorItem());

      const remove = new MenuItem('Delete...');
      remove.click.add(async () => {
        const result = await new ConfirmDialog('Delete ' + this.thing.name + '?').modal(this.form);
        if (result) {
          await this.thing.remove();
          map.updateZones();
        }
      });
      items.push(remove);

      return items;
    }
  }
}

export class MapView extends Control {
  private _zones: List<string>;
  private _container: ScrollBox;
  private _edit: CheckBox;
  private _zoneNames: Set<string> = new Set();
  private _lastZone: string;
  private _interval: number;

  constructor() {
    super();
    this.border = true;

    this._container = this.add(new ScrollBox(), 0, 0, null, null, 0, 0);

    this._zones = this.add(new List<string>(TextListItem), { x2: 10, w: 120, y: 10 });
    this._zones.coords.h.fit();

    this._zones.change.add(() => {
      this.update();
    });

    this._edit = this.add(new CheckBox('Edit'), { x2: 10, y2: 10, w: 80 });
    this._edit.toggle.add(() => {
      this.update();
    });

    this.update();

    this._interval = window.setInterval(() => {
      if (!this.editing) {
        this.update();
      }
    }, 1000);
  }

  get editing() {
    return this._edit.checked;
  }

  get zones() {
    return this._zoneNames.keys();
  }

  updateZones() {
    this._zoneNames.clear();
    this._zones.clear();
    this.update();
  }

  protected removed() {
    window.clearTimeout(this._interval);
  }

  async update() {
    const things = await Thing.load();
    this._container.clear();

    const zones = new Set<string>();
    if (this._zones.controls.length === 0) {
      this._zoneNames.clear();

      for (const thing of things) {
        if (thing.zone) {
          zones.add(thing.zone);
          this._zoneNames.add(thing.zone);
        }
      }
      if (zones.size === 0) {
        return;
      }

      const sortedZones = [...zones].sort();
      if (!this._lastZone) {
        this._lastZone = sortedZones[0];
      }
      for (const zone of sortedZones) {
        const z = this._zones.addItem(zone);
        if (zone === this._lastZone) {
          z.selected = true;
        }
      }
      return;
    }

    this._lastZone = this._zones.selectedItem;

    let maxX = 0;

    for (const thing of things) {
      if (thing.zone !== this._lastZone) {
        continue;
      }
      const mapThing = this._container.add(new MapThing(thing));
      mapThing.coords.w.fit();
      mapThing.coords.h.fit();
      if (this.editing) {
        const grabber = this._container.add(new Grabber(Math.max(0, thing.location.x - 20), Math.max(0, thing.location.y - 20)));
        grabber.setSnap(CoordAxis.X, 20);
        grabber.setSnap(CoordAxis.Y, 20);
        grabber.coords.size(20, 20);
        mapThing.coords.x.align(grabber.coords.xw);
        mapThing.coords.y.align(grabber.coords.yh);
        grabber.moved.add(() => {
          thing.location.x = mapThing.x;
          thing.location.y = mapThing.y;
          thing.save();
        }, 500);
      } else {
        mapThing.coords.x.set(thing.location.x);
        mapThing.coords.y.set(thing.location.y);
      }

      maxX = Math.max(maxX, thing.location.x);
    }

    this._container.add(new Spacer(), maxX + 200, 0, 10, 10);
  }
}
