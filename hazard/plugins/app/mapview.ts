import { Label, ScrollBox, Control, TextListItem, List, Ionicons, CheckBox, Grabber, CoordAxis } from "canvas-forms";
import { Thing } from './hazard';
import { ThingDialog } from "./thinglist";

class MapThing extends Control {
  constructor(readonly thing: Thing) {
    super();

    const l = this.add(new Label(), 0, 0);
    l.setIcon(Ionicons.Bulb);
    l.setFont(null, 40);
    l.fit = true;

    this.mousedown.add((ev) => {
      ev.capture();
      ev.cancelBubble();
    });
    this.mousemove.add((ev) => {
      // TODO: Drag.
    });
    this.mouseup.add((ev) => {
      if (ev.capture && ev.inside()) {
        new ThingDialog(this.thing).modal(this.form());
      }
    });
  }
}

export class MapView extends Control {
  zones: List<string>;
  container: ScrollBox;
  edit: CheckBox;

  constructor() {
    super();
    this.border = true;

    this.container = this.add(new ScrollBox(), 0, 0, null, null, 0, 0);

    this.zones = this.add(new List<string>(TextListItem), { x2: 10, w: 80, y: 10 });
    this.zones.coords.h.fit();

    this.zones.change.add(() => {
      this.update();
    });

    this.edit = this.add(new CheckBox('Edit'), { x2: 10, y2: 10, w: 80 });
    this.edit.toggle.add(() => {
      this.update();
    });

    this.update();
  }

  async update() {
    this.container.clear();

    const things = await Thing.load();

    const zones = new Set<string>();
    if (this.zones.controls.length === 0) {
      for (const thing of things) {
        if (thing.zone) {
          zones.add(thing.zone);
        }
      }
      let first = true;
      for (const zone of zones) {
        const z = this.zones.addItem(zone);
        if (first) {
          z.setSelected(true);
        }
        first = false;
      }
      return;
    }

    for (const thing of things) {
      if (thing.zone !== this.zones.selected()) {
        continue;
      }
      const mapThing = this.container.add(new MapThing(thing));
      mapThing.coords.w.fit();
      mapThing.coords.h.fit();
      if (this.edit.checked) {
        const grabber = this.container.add(new Grabber(thing.location.x - 20, thing.location.y - 20));
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
    }
  }
}
