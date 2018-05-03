<zigbee-bind-list>
  <div onclick={toggle}>Bind</div>
  <ul show={show}>
    <li each={cluster in clusters}>
      <zigbee-bind device={opts.device} endpoint={opts.endpoint} cluster={cluster}></zigbee-bind>
    </li>
  </ul>
  <script>
   this.show = false;
   this.clusters = [];

   this.toggle = async function() {
     this.show = !this.show;

     if (this.show) {
       let spec = await loadSpec();
       this.clusters = [];
       for (let cluster of spec['cluster']) {
         if (opts.endpoint.out_clusters.indexOf(cluster.cluster) >= 0) {
           this.clusters.push(cluster);
         }
       }
       console.log(this.clusters);
       this.update();
     }
   }
  </script>
</zigbee-bind-list>

<zigbee-bind>
  <div>{opts.cluster.name} <button onclick={bind}>Bind</button></div>
  <div>
    <textarea style="width: 500px; height: 100px;" show={response_json}>{response_json}</textarea>
  </div>
  <script>
   this.response_json = '';

   this.bind = async function() {
     let status = await loadStatus();

     let response = await sendZdo(opts.device, 'bind', {
       'src_addr': opts.device.addr64,
       'src_ep': opts.endpoint.endpoint,
       'cluster': opts.cluster.cluster,
       'dst_addr_mode': 3,  // 64-bit device.
       'dst_addr': status['coordinator_addr64'],
       'dst_ep': 1,
     });
     this.response_json = JSON.stringify(response, null, '  ');
     this.update();
   }
  </script>
</zigbee-bind>
