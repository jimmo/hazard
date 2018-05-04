<hazard-thing-list class="{classes}">
  <hazard-thing each="{thing in groups}" thing="{thing}"></hazard-thing>
  <br>
  <hazard-thing each="{thing in things}" thing="{thing}"></hazard-thing>
  <script>
   this.groups = [];
   this.things = [];

   this.classes = {
     'map': this.opts.mode === 'map',
     'list': this.opts.mode === 'list',
   };

   this.on('mount', async function() {
     this.groups = [];
     this.things = [];
     for (const t of await loadThings()) {
       if (thingHasFeature(t, 'group')) {
         this.groups.push(t);
       } else {
         this.things.push(t);
       }
     }
     this.groups.sort(sortHelper('zone', 'type', 'name'));
     this.things.sort(sortHelper('zone', 'type', 'name'));
     this.update();
   });
  </script>
</hazard-thing-list>

<hazard-thing style="{styles}" class="{classes}">
  <h1>
    <icon class="{icon_classes}"></icon>
    <span class="name">{opts.thing.name}</span>
  </h1>
  <hazard-thing-popup thing="{opts.thing}">
    <button class="edit" onclick="{edit_click}"><icon class="ion-edit"></icon></button>
    <input type="text" class="name" onchange="{save_thing}" data-field="name" value="{opts.thing.name}">
    <h5 class="zone" if="{opts.thing.zone}">{opts.thing.zone}</h5>

    <div class="editor" if="{editing}">
      <label>X: <input type="text" value="{opts.thing.location.x}" onchange="{save_thing}" data-field="location.x"></label>
      <label>Y: <input type="text" value="{opts.thing.location.y}" onchange="{save_thing}" data-field="location.y"></label>
      <label if="{opts.thing.size}">Width: <input type="text" value="{opts.thing.size.w}" onchange="{save_thing}" data-field="size.w"></label>
      <label if="{opts.thing.size}">Height: <input type="text" value="{opts.thing.size.h}" onchange="{save_thing}" data-field="size.h"></label>

      <hazard-thing-switch-editor if="{has_feature('switch')}" thing="{opts.thing}"></hazard-thing-switch-editor>
    </div>

    <div if="{!editing}">
      <hazard-thing-switch if="{has_feature('switch')}" thing="{opts.thing}"></hazard-thing-switch>
      <hazard-thing-light if="{has_feature('light')}" thing="{opts.thing}"></hazard-thing-light>
      <hazard-thing-light-level if="{has_feature('light-level')}" thing="{opts.thing}"></hazard-thing-light-level>
      <hazard-thing-light-color if="{has_feature('light-color')}" thing="{opts.thing}"></hazard-thing-light-color>
      <hazard-thing-light-temperature if="{has_feature('light-temperature')}" thing="{opts.thing}"></hazard-thing-light-temperature>
    </div>
  </hazard-thing-popup>
  <style>
   :scope {
   }
   :scope h1 {
     font-size: 16px;
     font-weight: normal;
   }

   .list :scope {
     position: relative;
     display: block;
     border: 1px solid silver;
     padding: 3px;
     margin: 2px;
     width: 200px;
     border-radius: 2px;
   }
   .list :scope h1 {
     padding-left: 3px;
   }
   .list :scope h1 icon {
     width: 32px;
     text-align: center;
     display: inline-block;
     font-size: 20px;
   }

   .map :scope {
     position: absolute;
     width: 48px;
     height: 48px;
   }
   .map :scope h1 {
     text-align: center;
   }
   .map :scope h1 icon {
     font-size: 32px;
     text-shadow: 2px 2px 1px #c0c0c0c0;
   }
   .map :scope h1 .name {
     display: none;
   }

   hazard-thing-popup {
     opacity: 0;
     display: block;
     visibility: hidden;
     position: absolute;
     width: 200px;
     border: 1px solid black;
     box-shadow: 2px 2px 2px #c0c0c0c0;
     border-radius: 4px;
     background-color: white;
     z-index: 1;
     padding: 5px;
     transition: opacity 0.5s ease, visibility 0.5s;
   }
   :scope.editing hazard-thing-popup {
     width: 400px;
   }
   hazard-thing-popup .edit {
     position: absolute;
     right: 10px;
     top: 5px;
     width: 32px;
     height: 32px;
   }
   hazard-thing-popup input.name {
     border: 1px solid white;
     font-family: inherit;
     font-size: 18px;
     font-weight: bold;
     width: 100%;
   }

   .list :scope hazard-thing-popup {
     left: 180px;
     top: 10px;
   }
   .map :scope hazard-thing-popup {
     left: 30px;
     top: 20px;
   }

   :scope:hover hazard-thing-popup {
     opacity: 1;
     visibility: visible;
   }
   hazard-thing-popup .editor {
     padding-top: 10px;
   }
   hazard-thing-popup .editor label {
     width: 100%;
     display: block;
     position: relative;
     padding: 3px;
   }
   hazard-thing-popup .editor label input {
     width: 65%;
     position: absolute;
     right: 5px;
   }
  </style>
  <script>
   this.editing = false;

   edit_click() {
     this.editing = !this.editing;
     this.classes['editing'] = this.editing;
   }

   has_feature(f) {
     return thingHasFeature(this.opts.thing, f);
   }

   calculate_styles() {
     const style = {
     };
     if (this.parent.opts.mode === 'map') {
       style['left'] = this.opts.thing.location.x + 'px';
       style['top'] = this.opts.thing.location.y + 'px';
       if (this.opts.thing.size) {
         style['width'] = this.opts.thing.size.w + 'px';
         style['height'] = this.opts.thing.size.h + 'px';
       }
     }
     return style;
   }

   calculate_icon() {
     return {
       'ion-lightbulb': this.has_feature('light'),
       'ion-toggle': this.has_feature('switch'),
     };
   }

   async save_thing(e) {
     const field = e.currentTarget.dataset.field.split('.');
     let t = this.opts.thing;
     for (let i = 0; i < field.length - 1; ++i) {
       t = t[field[i]];
     }
     t[field[field.length-1]] = e.currentTarget.value;
     await thingSave(this.opts.thing);
   }

   this.styles = this.calculate_styles();
   this.icon_classes = this.calculate_icon();
   this.classes = {
     'editing': false,
   };
  </script>
</hazard-thing>

<hazard-thing-switch>
  <hazard-thing-switch-button each="{button, i in opts.thing.buttons}" button="{button}" index="{i}" thing="{parent.opts.thing}">
  </hazard-thing-switch-button>
  <style>
   :scope {
     display: block;
   }
  </style>
  <script>
  </script>
</hazard-thing-switch>

<hazard-thing-switch-button>
  <button onclick="{click}">
    {opts.index + 1}
  </button>
  <style>
   :scope button {
     margin: 2px;
     width: 32px;
     height:32px;
     border-radius: 3px;
     border: 1px outset silver;
     cursor: pointer;
   }
  </style>
  <script>
   async click() {
     thingAction(opts.thing, 'tap', {
       'button': opts.index,
     });
   };
  </script>
</hazard-thing-switch-button>

<hazard-thing-switch-editor>
  <hazard-thing-switch-editor-button each="{button, i in opts.thing.buttons}" button="{button}" index="{i}" thing="{parent.opts.thing}">
  </hazard-thing-switch-editor-button>
  <style>
   :scope {
     display: block;
   }
  </style>
  <script>
  </script>
</hazard-thing-switch-editor>

<hazard-thing-switch-editor-button>
  <label>Button {opts.index + 1}</label>
  <div each="{code, name in opts.button.code}">
    <label>{name}</label>
    <textarea onchange="{save_button}" data-name="{name}">{code}</textarea>
  </div>
  <style>
   :scope {
     margin: 2px;
   }
   :scope label {
     padding: 1px;
   }
   :scope div label {
     font-size: 12px;
     padding: 0px;
   }
   :scope div textarea {
     width: 100%;
     height: 80px;
   }
  </style>
  <script>
   async save_button(e) {
     this.opts.thing.buttons[this.opts.index].code[e.currentTarget.dataset.name] = e.currentTarget.value;
     await thingSave(this.opts.thing);
   }
  </script>
</hazard-thing-switch-editor-button>

<hazard-thing-light>
  <button onclick="{on}"><icon class="ion-toggle-filled"></icon></button>
  <button onclick="{off}"><icon class="ion-toggle"></icon></button>
  <button onclick="{toggle}"><icon class="ion-arrow-swap"></icon></button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
   :scope button {
     margin: 2px;
     height:32px;
     border-radius: 3px;
     border: 1px outset silver;
     cursor: pointer;
     font-size: 20px;
   }
  </style>
  <script>
   async on() {
     thingAction(opts.thing, {
       'action': 'on',
     });
   }
   async off() {
     thingAction(opts.thing, {
       'action': 'off',
     });
   }
   async toggle() {
     thingAction(opts.thing, 'toggle', {
     });
   }
  </script>
</hazard-thing-light>

<hazard-thing-light-level>
  <button each="{level in generate_levels()}" click="{click}" data-level="{level.level}"><icon class="ion-ios-sunny" style="{level.style}"></icon></button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
   :scope button {
     margin: 2px;
     height: 32px;
     width: 32px;
     border-radius: 3px;
     border: 1px outset silver;
     cursor: pointer;
     font-size: 20px;
   }
  </style>
  <script>
   generate_levels() {
     const levels = [];
     for (let i = 0; i < 5; ++i) {
       levels.push({'level': i/5, 'style': {'opacity': i/5}});
     }
     return levels;
   }
   async click(e) {
     thingAction(opts.thing, 'level', {
       'level': parseFloat(e.currentTarget.dataset.level),
     });
   }
  </script>
</hazard-thing-light-level>

<hazard-thing-light-color>
  <button>color</button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
  </style>
  <script>
  </script>
</hazard-thing-light-color>

<hazard-thing-light-temperature>
  <button each="{temp in generate_temps()}" onclick="{click}" data-temp="{temp.temp}"><icon class="ion-thermometer" style="{temp.style}"></icon></button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
   :scope button {
     margin: 2px;
     height: 32px;
     width: 32px;
     border-radius: 3px;
     border: 1px outset silver;
     cursor: pointer;
     font-size: 20px;
   }
  </style>
  <script>
   generate_temps() {
     const temps = [];
     for (let i = 0; i < 5; ++i) {
       let r = 0 + i * 50;
       let g = 128;
       let b = 255 - i*50;
       temps.push({'temp': i/5, 'style': {'color': 'rgb(' + r + ',' + g + ',' + b + ')'}});
     }
     return temps;
   }
   async click(e) {
     thingAction(opts.thing, 'temperature', {
       'temperature': parseFloat(e.currentTarget.dataset.temp),
     });
   }
  </script>
</hazard-thing-light-temperature>
