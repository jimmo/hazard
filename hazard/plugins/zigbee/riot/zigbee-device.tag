<zigbee-device>
  <h4 onclick={click}>{opts.device.addr64} / {opts.device.addr16} / <input type="text" value={opts.device.name} onchange={update_name}></h4>
  <ul>
    <li>
      <zigbee-zdo-list device={opts.device}></zigbee-zdo-list>
    </li>
    <li>
      <div onclick={toggle}>Endpoints</div>
      <ul show_endpoints={show_endpoints}>
        <li each={endpoint in endpoints}>
          {endpoint.profile.name} / {endpoint.endpoint}
          <ul>
            <li>
              <zigbee-command-list device={opts.device} endpoint={endpoint}></zigbee-command-list>
            </li>
            <li>
              <zigbee-bind-list device={opts.device} endpoint={endpoint}></zigbee-bind-list>
            </li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <select id="thing-types">
        <option each="{thing in thing_types}" value="{thing.type}">{thing.type}</option>
      </select>
      <button onclick="{create}">Create</button>
    </li>
  </ul>
  <script>
   this.endpoints = [];
   this.show_endpoints = true;
   this.thing_types = [];

   this.on('mount', async function() {
     this.thing_types = await loadThingTypes();
     this.update();
   });

   async update_name(e) {
     await renameDevice(opts.device, e.target.value);
   };

   async toggle() {
     if (this.show_endpoints) {
       this.endpoints = await loadEndpoints(opts.device);
       this.update();
     }
     this.show_endpoints = !this.show_endpoints;
     this.update();
   };

   async create() {
     await createThingFromDevice(opts.device, this.root.querySelector('#thing-types').value);
   }
  </script>
</zigbee-device>
