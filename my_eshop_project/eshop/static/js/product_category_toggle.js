////////////////////////////////////////////////////
// product_category_toggle.js
////////////////////////////////////////////////////
(function() {
    document.addEventListener('DOMContentLoaded', function() {
      
      // 1) The Category <select> typically has ID = "id_category".
      const categorySelect = document.getElementById('id_category');
      if (!categorySelect) return; // no category field found
  
      //////////////////////////////////////////////
      // Lists of fields to hide for each top-level
      //////////////////////////////////////////////
      const fieldsNotForVFD = [
        'plc_input',
        'plc_output',
        'display_device',
        // add more if needed...
      ];
      const fieldsNotForPLC = [
        'rated_output_power',
        'rated_output_current',
        'input_frequency',
        'output_frequency_range',
        'display_device',
        // ...
      ];
      const fieldsNotForHMI = [
        'rated_output_power',
        'rated_output_current',
        'input_frequency',
        'output_frequency_range',
        'plc_input',
        'plc_output',
        // ...
      ];
      const fieldsNotForSERVO = [
        'input_frequency',
        'output_frequency_range',
        'plc_input',
        'plc_output',
        'display_device',
        // ...
      ];
  
      // All fields in the "Technical Specifications"
      const allSpecFields = [
        'rated_output_power',
        'rated_output_current',
        'input_frequency',
        'output_frequency_range',
        'output_voltage',
        'plc_input',
        'plc_output',
        'supply_voltage',
        'output_type',
        'display_device',
        'screen_size',
        'external_dimensions',
        'resolution',
        'display_size',
        'display_color',
        'rated_torque',
        'maximum_torque',
        'rated_speed',
        'maximum_speed',
        'power_supply_capacity',
        'power_supply_input',
        'rated_voltage',
        'rated_current',
        'maximum_current',
        'control_method',
        'dynamic_brake',
        'encoder_type',
        'communication',
        'encoder_resolution',
        'servo_motor',
        'servo_amplifier'
      ];
  
      //////////////////////////////////////////////
      // Detect the top-level name from the
      // chosen category
      //////////////////////////////////////////////
      function getTopCategoryName() {
        // In Django admin, the selected option might be "---- SERVO"
        // or "VFD > D Series" etc. We'll parse the text
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        if (!selectedOption) return '';
        const text = selectedOption.textContent.toUpperCase();
  
        if (text.includes('VFD')) return 'VFD';
        if (text.includes('PLC')) return 'PLC';
        if (text.includes('HMI')) return 'HMI';
        if (text.includes('SERVO')) return 'SERVO';
        return '';
      }
  
      //////////////////////////////////////////////
      // Hide or show a list of field rows
      //////////////////////////////////////////////
      function hideFields(fieldNames) {
        fieldNames.forEach(fieldName => {
          const fieldInput = document.getElementById(`id_${fieldName}`);
          if (fieldInput) {
            const parentRow = fieldInput.closest('.form-row') 
                             || fieldInput.closest('.row') 
                             || fieldInput.closest('.form-group');
            if (parentRow) {
              parentRow.style.display = 'none';
            }
          }
        });
      }
  
      function showFields(fieldNames) {
        fieldNames.forEach(fieldName => {
          const fieldInput = document.getElementById(`id_${fieldName}`);
          if (fieldInput) {
            const parentRow = fieldInput.closest('.form-row') 
                             || fieldInput.closest('.row') 
                             || fieldInput.closest('.form-group');
            if (parentRow) {
              parentRow.style.display = ''; // default
            }
          }
        });
      }
  
      //////////////////////////////////////////////
      // Update the UI based on the chosen category
      //////////////////////////////////////////////
      function updateFieldsDisplay() {
        // 1) Show everything initially (so we can "reset")
        showFields(allSpecFields);
  
        // 2) Identify top-level
        const top = getTopCategoryName();
        if (top === 'VFD') {
          hideFields(fieldsNotForVFD);
        } else if (top === 'PLC') {
          hideFields(fieldsNotForPLC);
        } else if (top === 'HMI') {
          hideFields(fieldsNotForHMI);
        } else if (top === 'SERVO') {
          hideFields(fieldsNotForSERVO);
        }
      }
  
      // 3) Fire once on load
      updateFieldsDisplay();
  
      // 4) Also listen for changes
      categorySelect.addEventListener('change', function() {
        updateFieldsDisplay();
      });
    });
  })();
  