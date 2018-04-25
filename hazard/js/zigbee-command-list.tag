<zigbee-command-list>
  <div onclick={toggle}>Commands</div>
  <ul hide={hide}>
    <li each={cluster in clusters}>
      {cluster.name}
      <ul>
        <li each={command in cluster.rx_commands}>
          <zigbee-command device={opts.device} endpoint={opts.endpoint} cluster={cluster} command={command}>
          </zigbee-command>
        </li>
      </ul>
    </li>
  </ul>
  <script>
   this.hide = true;
   this.clusters = [];

   this.toggle = function() {
     this.hide = !this.hide;
   }

   this.on('mount', async function() {
     let spec = await loadSpec();
     this.clusters = [];
     for (let cluster of spec['cluster']) {
       if (opts.endpoint.in_clusters.indexOf(cluster.cluster) >= 0) {
         this.clusters.push(cluster);
       }
     }
     this.update();
   });
  </script>
</zigbee-command-list>

<zigbee-command>
  <div onclick={toggle}>{opts.command.name}</div>
  <div hide={hide}>
    <textarea style="width:500px;height:200px;" oninput={edit}>{request_json}</textarea>
    <button onclick={send}>Send</button>
  </div>
  <div hide={hide || !response_json}>
    <textarea style="width:500px;height:100px;">{response_json}</textarea>
  </div>
  <script>
   this.hide = true;
   this.request_json = '';
   this.response_json = '';

   this.toggle = function() {
     this.hide = !this.hide;
   };

   this.edit = function(e) {
     this.request_json = e.target.value;
   }

   this.on('mount', async function() {
     let obj = {};
     for (let arg of opts.command.args) {
       arg = arg.split(':');
       obj[arg[0]] = arg[1];
       if (arg[0] === 'addr16') {
         obj[arg[0]] = opts.device.addr16;
       }
       if (arg[0] === 'addr64') {
         obj[arg[0]] = opts.device.addr64;
       }
     }
     this.request_json = JSON.stringify(obj, null, ' ');
     this.update();
   });

   this.send = async function() {
     let response = await sendZclCluster(opts.device, opts.endpoint, opts.cluster.name, opts.command.name, JSON.parse(this.request_json));
     this.response_json = JSON.stringify(response, null, ' ');
     this.update();
   };
  </script>
</zigbee-command>
