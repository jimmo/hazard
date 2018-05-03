<zigbee-zdo-list>
  <div onclick={toggle}>ZDO</div>
  <ul hide={hide}>
    <li each={zdo in zdos}>
      <zigbee-zdo zdo={zdo} device={opts.device}></zigbee-zdo>
    </li>
  </ul>
  <script>
   this.hide = true;
   this.zdos = [];

   this.toggle = async function() {
     if (this.hide) {
       let spec = await loadSpec();
       this.zdos = spec['zdo'];
       console.log(this.zdos);
       this.update();
     }
     this.hide = !this.hide;
     this.update();
   }
  </script>
</zigbee-zdo-list>

<zigbee-zdo>
  <div onclick={toggle}>{opts.zdo.cluster_name}</div>
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
     for (let arg of opts.zdo.args) {
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
     let response = await sendZdo(opts.device, opts.zdo.cluster_name, JSON.parse(this.request_json));
     this.response_json = JSON.stringify(response, null, ' ');
     this.update();
   };
  </script>
</zigbee-zdo>
