/* Gold ERP - Scrap Alarm Logic */
document.addEventListener('DOMContentLoaded', function () {

    // Config: Allowable Loss Threshold (3%)
    const MAX_LOSS_PERCENT = 3.0;

    // Select Fields (ID format in Django admin is typically id_field_name)
    const inputWeightField = document.getElementById('id_input_weight');
    const outputWeightField = document.getElementById('id_output_weight');
    const scrapWeightField = document.getElementById('id_scrap_weight');

    if (!inputWeightField || !outputWeightField) return;

    // Create warning elements
    const warningDiv = document.createElement('div');
    warningDiv.id = 'scrap-warning-box';
    warningDiv.style.display = 'none';
    warningDiv.style.marginTop = '15px';
    warningDiv.style.padding = '15px';
    warningDiv.style.background = 'rgba(255, 75, 43, 0.15)';
    warningDiv.style.border = '1px solid #ff4b2b';
    warningDiv.style.borderRadius = '10px';
    warningDiv.style.color = '#ff4b2b';
    warningDiv.style.fontWeight = 'bold';
    warningDiv.style.textAlign = 'center';
    warningDiv.style.animation = 'pulse-red 1s infinite';

    // Insert after input section (approx location)
    const weightsGroup = document.querySelector('.field-input_weight').closest('fieldset');
    if (weightsGroup) {
        weightsGroup.appendChild(warningDiv);
    }

    // Add Keyframes for pulse
    const styleSheet = document.createElement("style");
    styleSheet.innerText = `
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(255, 75, 43, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0); }
        }
    `;
    document.head.appendChild(styleSheet);


    function calculateLoss() {
        const inputVal = parseFloat(inputWeightField.value) || 0;
        const outputVal = parseFloat(outputWeightField.value) || 0;

        if (inputVal > 0) {
            // Calculate current loss
            let scrapVal = parseFloat(scrapWeightField.value) || 0;

            // If scrap field is empty, assume calc: input - output
            // But usually we want to just check if input - (output + scrap) is balanced, 
            // OR checks the Ratio of Scrap vs Input.

            // Let's assume User enters Input and Output. The difference is potential scrap.
            let calculatedScrap = inputVal - outputVal;

            // If user explicitly entered scrap, use that to check total balance
            if (scrapWeightField.value) {
                calculatedScrap = parseFloat(scrapWeightField.value);
            }

            const lossPercent = (calculatedScrap / inputVal) * 100;

            if (lossPercent > MAX_LOSS_PERCENT) {
                // Danger!
                showAlarm(lossPercent);
            } else {
                hideAlarm();
            }
        }
    }

    function showAlarm(percent) {
        warningDiv.style.display = 'block';
        warningDiv.innerHTML = `
            <i class="fa-solid fa-bell fa-shake" style="font-size:1.5rem; margin-bottom:10px; display:block;"></i>
            تحذير: نسبة الخسية مرتفعة جداً (${percent.toFixed(2)}%)
            <br>
            <span style="font-size:0.8rem; font-weight:normal;">المسموح به: ${MAX_LOSS_PERCENT}%</span>
        `;
        playBeep();

        // Highlight fields
        inputWeightField.style.borderColor = '#ff4b2b';
        outputWeightField.style.borderColor = '#ff4b2b';
    }

    function hideAlarm() {
        warningDiv.style.display = 'none';
        inputWeightField.style.borderColor = ''; // Reset
        outputWeightField.style.borderColor = ''; // Reset
    }

    // Oscillator Beep function (No external file needed)
    function playBeep() {
        // Prevent spamming
        if (window.audioContext && window.audioContext.state === 'running') return;

        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        const ctx = new AudioContext();
        window.audioContext = ctx; // Cache it

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle'; // Alert sound
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 0.1); // Rising alarm pitch

        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    }

    // Listen events
    inputWeightField.addEventListener('input', calculateLoss);
    outputWeightField.addEventListener('input', calculateLoss);
    if (scrapWeightField) scrapWeightField.addEventListener('input', calculateLoss);

    // --- NEW: Colorize Tabular Inline Loss Fields ---
    function colorizeLossFields() {
        // Target readonly fields in tabular inline
        const lossCells = document.querySelectorAll('.field-loss_weight p, .field-loss_weight .readonly');
        
        lossCells.forEach(cell => {
            const text = cell.innerText || cell.textContent;
            const val = parseFloat(text);

            if (!isNaN(val)) {
                // Reset basic style
                cell.style.fontWeight = '900';
                cell.style.fontSize = '1.1rem'; // Make numbers bigger/clearer
                cell.style.borderRadius = '4px';
                cell.style.padding = '2px 6px';
                cell.style.display = 'inline-block';

                if (val < 0) {
                    // Gain (Negative) -> Green
                    cell.style.color = '#00e676'; // Bright Green
                    cell.style.backgroundColor = 'rgba(0, 230, 118, 0.1)';
                    cell.style.border = '1px solid rgba(0, 230, 118, 0.3)';
                } else if (val > 0) {
                    // Loss (Positive) -> Red
                    cell.style.color = '#ff1744'; // Bright Red
                    // cell.style.backgroundColor = 'rgba(255, 23, 68, 0.1)'; // Optional bg for red too
                } else {
                    // Zero
                    cell.style.color = '#aaa';
                }
            }
        });
    }

    // Run on load
    colorizeLossFields();
    
    // Run periodically to catch dynamic updates if needed (though loss is mainly server-side)
    setInterval(colorizeLossFields, 2000);
});
