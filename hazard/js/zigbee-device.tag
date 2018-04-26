<zigbee-device>
  <h4 onclick={click}>{opts.device.addr64} / {opts.device.addr16} / <input type="text" value={opts.device.name} onchange={update_name}></h4>
  <ul>
    <li>
      <zigbee-zdo-list device={opts.device}></zigbee-zdo-list>
    </li>
    <li>
      <div onclick={toggle}>Endpoints</div>
      <ul hide={hide}>
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
  </ul>
  <script>
   this.endpoints = [];
   this.hide = true;

   this.update_name = async function(e) {
     await renameDevice(opts.device, e.target.value);
   };

   this.toggle = async function() {
     if (this.hide) {
       this.endpoints = await loadEndpoints(opts.device);
       this.update();
     }
     this.hide = !this.hide;
     this.update();
   };
  </script>
</zigbee-device>
