import { List, ClickableListItem, Label, TextAlign, MenuItems, MenuItem, ConfirmDialog, PromptDialog, TextBox, CoordAxis, Dialog, Button, MenuSeparatorItem } from "canvas-forms";
import { Action } from './hazard';
import { sortBy } from './utils';

class ActionCodeDialog extends Dialog {
  constructor(readonly action: Action) {
    super();

    let l = this.add(new Label('Code'), 10, 10);
    l.fit = true;
    const code = this.add(new TextBox(action.code), { x: 10, y: 40, x2: 10, y2: 80 });
    code.fontName = 'monospace';
    code.multiline = true;

    this.add(new Button('Cancel'), { x2: 20, y2: 20 }).click.add(() => {
      this.close(null);
    });
    this.add(new Button('OK'), { x2: 190, y2: 20 }).click.add(() => {
      this.action.code = code.text;
      this.action.save();
      this.close(null);
    });
  }

  defaultConstraints() {
    // Override Dialog default which centers a fixed width/height dialog in the form.
    this.coords.x.set(20);
    this.coords.x2.set(20);
    this.coords.h.set(380)
    this.coords.center(CoordAxis.Y);
  }

}


class ActionListItem extends ClickableListItem<Action> {
  constructor(readonly action: Action) {
    super(action);

    this.border = true;

    const l = this.add(new Label(action.name), { x: 3, y: 3, x2: 3, y2: 3 });
    l.align = TextAlign.CENTER;
    l.fontSize = 22;

    this.click.add((ev) => {
      this.action.invoke();
    });
  }

  protected async contextMenu(): Promise<MenuItems> {
    const edit = new MenuItem('Edit code');
    edit.click.add(async () => {
      await new ActionCodeDialog(this.action).modal(this.form);
    });

    const rename = new MenuItem('Rename');
    rename.click.add(async () => {
      const result = await new PromptDialog('Rename action', this.action.name).modal(this.form);
      if (result) {
        this.action.name = result;
        this.action.save();
        (this.parent as ActionList).update();
      }
    });

    const remove = new MenuItem('Delete');
    remove.click.add(async () => {
      const result = await new ConfirmDialog('Delete action?').modal(this.form);
      if (result) {
        this.action.remove();
        (this.parent as ActionList).update();
      }
    });

    return [
      edit,
      rename,
      new MenuSeparatorItem(),
      remove,
    ]
  }

  defaultConstraints() {
    this.coords.h.set(60);
    return true;
  }
}

export class ActionList extends List<Action> {
  constructor() {
    super(ActionListItem);

    this.update();
  }

  async update() {
    this.clear();

    const actions = await Action.load();
    actions.sort(sortBy('name'));
    for (const action of actions) {
      const l = this.addItem(action);
    }
  }

  protected async contextMenu(): Promise<MenuItems> {
    const addNew = new MenuItem('Add new...');
    addNew.click.add(async () => {
      const a = await Action.create();
      await new ActionCodeDialog(a).modal(this.form);
      this.update();
    });

    return [addNew];
  }
}
