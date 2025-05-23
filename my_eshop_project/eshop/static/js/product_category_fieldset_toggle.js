// product_category_fieldset_toggle.js

(function(){
  document.addEventListener('DOMContentLoaded', function(){
      var catSelect = document.getElementById('id_category');
      if(!catSelect) return;

      // We locate the specialized fieldsets by their CSS classes:
      var vfdSets    = document.querySelectorAll('.vfd-fields');
      var plcSets    = document.querySelectorAll('.plc-fields');
      var hmiSets    = document.querySelectorAll('.hmi-fields');
      var servoSets  = document.querySelectorAll('.servo-fields');

      function hideAll(){
          [vfdSets,plcSets,hmiSets,servoSets].forEach(set=>{
              set.forEach(el=>{ el.style.display='none'; });
          });
      }

      function showEls(nodelist){
          nodelist.forEach(el=>{ el.style.display=''; });
      }

      function getTopCatName(){
          var opt = catSelect.options[catSelect.selectedIndex];
          if(!opt) return '';
          var text = (opt.textContent || '').toUpperCase();
          // You can do .includes('VFD') or exact match
          if(text.includes('VFD')) return 'VFD';
          if(text.includes('PLC')) return 'PLC';
          if(text.includes('HMI')) return 'HMI';
          if(text.includes('SERVO')) return 'SERVO';
          return '';
      }

      function updateVisibility(){
          hideAll();
          var c = getTopCatName();
          if(c === 'VFD')   showEls(vfdSets);
          if(c === 'PLC')   showEls(plcSets);
          if(c === 'HMI')   showEls(hmiSets);
          if(c === 'SERVO') showEls(servoSets);
      }

      // initial
      updateVisibility();

      // on change
      catSelect.addEventListener('change', updateVisibility);
  });
})();
