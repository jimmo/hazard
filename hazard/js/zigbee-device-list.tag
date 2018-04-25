<zigbee-device-list>
  <ul>
    <li each={device in devices}>
      <zigbee-device device="{device}"></zigbee-device>
    </li>
  </ul>
  <script>
   this.devices = [];

   this.on('mount', async function() {
     this.devices = await loadDevices();
     this.update();
   });
  </script>
</zigbee-device-list>
