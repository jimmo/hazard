<hazard-thing-list class={classes}>
  <hazard-thing each="{thing in things}" thing="{thing}">
  </hazard-thing>
  <script>
   this.things = [];
   this.classes = {
     'map': this.opts.mode === 'map',
     'list': this.opts.mode === 'list',
   };

   this.on('mount', async function() {
     this.things = await loadThings();
     this.update();
   });
  </script>
</hazard-thing-list>

<hazard-thing style="{styles}">
  <h1>
    <icon class="far fa-lightbulb"></icon>
    <span class="name">{opts.thing.name}</span>
  </h1>
  <hazard-thing-popup thing="{opts.thing}">
    <input type="text" class="name" onchange="{update_name}" value="{opts.thing.name}">
    <h5 class="zone" if="{opts.thing.zone}">{opts.thing.zone}</h5>
    <hazard-thing-switch if="{has_feature('switch')}" thing="{opts.thing}"></hazard-thing-switch>
    <hazard-thing-light if="{has_feature('light')}" thing="{opts.thing}"></hazard-thing-light>
    <hazard-thing-light-level if="{has_feature('light-level')}" thing="{opts.thing}"></hazard-thing-light-level>
    <hazard-thing-light-color if="{has_feature('light-color')}" thing="{opts.thing}"></hazard-thing-light-color>
    <hazard-thing-light-temperature if="{has_feature('light-temperature')}" thing="{opts.thing}"></hazard-thing-light-temperature>
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
     left: 30px;
     top: 20px;
     width: 200px;
     border: 1px solid black;
     box-shadow: 2px 2px 2px #c0c0c0c0;
     border-radius: 4px;
     background-color: white;
     z-index: 1;
     padding: 5px;
     transition: opacity 0.5s ease, visibility 0.5s;
   }
   hazard-thing-popup input.name {
     border: 1px solid white;
     font-family: inherit;
     font-size: 18px;
     font-weight: bold;
     width: 100%;
   }

   :scope:hover hazard-thing-popup {
     opacity: 1;
     visibility: visible;
   }
  </style>
  <script>
   has_feature(f) {
     return this.opts.thing.features.indexOf(f) >= 0;
   }

   calculate_styles() {
     const style = {
     };
     if (this.parent.opts.mode === 'map') {
       if (this.opts.thing.location) {
         style['left'] = this.opts.thing.location.x + 'px';
         style['top'] = this.opts.thing.location.y + 'px';
       } else {
         style['left'] = this.opts.thing.bounds.x + 'px';
         style['top'] = this.opts.thing.bounds.y + 'px';
         style['width'] = this.opts.thing.bounds.w + 'px';
         style['height'] = this.opts.thing.bounds.h + 'px';
       }
     }
     return style;
   }

   async update_name(e) {
     this.opts.thing.name = e.currentTarget.value;
     await thingSave(this.opts.thing);
   }

   this.styles = this.calculate_styles();

  </script>
</hazard-thing>

<hazard-thing-switch>
  <hazard-thing-switch-button each="{button, i in opts.thing.buttons}" button="{i}" thing="{parent.opts.thing}">
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
    {opts.button}
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
       'button': opts.button,
     });
   };
  </script>
</hazard-thing-switch-button>

<hazard-thing-light>
  <button onclick="{on}"><icon class="fas fa-toggle-off"></icon></button>
  <button onclick="{off}"><icon class="fas fa-toggle-on"></icon></button>
  <button onclick="{toggle}"><icon class="fas fa-exchange-alt"></icon></button>
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
  <button each="{level in generate_levels()}" click="{click}" data-level="{level.level}"><icon class="far fa-lightbulb" style="{level.style}"></icon></button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
   :scope button {
     margin: 2px;
     height: 32px;
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
  <button each="{temp in generate_temps()}" onclick="{click}" data-temp="{temp.temp}"><icon class="far fa-lightbulb" style="{temp.style}"></icon></button>
  <style>
   :scope {
     display: block;
     margin-top: 5px;
   }
   :scope button {
     margin: 2px;
     height: 32px;
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
       let r = 255 - i*40;
       let g = 150;
       let b = 0 + i*40;
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
