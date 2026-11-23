/**
 * LIV-SENSI AI – HOLOGRAPHIC NEURAL HEART & CARDIOVASCULAR AI CONSOLE
 * 3D Holographic Heart with Real-Time EKG Pulse Waveform, Interactive BPM Telemetry,
 * Dynamic Parallax 3D Tilt, and Clinical Biometrics HUD
 * Palette: Deep Purple (#812D80) & Electric Magenta (#E52591) on Obsidian Studio Dark (#0B070D / #170E1A)
 */

class HolographicCardioController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.currentPreset = 'normal';
    this.bpm = 74;
    this.pulseSpeed = 1.1; // seconds
    this.isPinsVisible = true;
    this.isEkgVisible = true;

    this.presets = {
      rest: {
        id: 'rest',
        title: 'Resting Sinus',
        bpm: 60,
        speed: 1.35,
        status: 'Resting Sinus Rhythm',
        statusColor: '#10B981',
        strokeVol: '72 mL',
        cardiacOutput: '4.3 L/min',
        perfusion: '99.6%',
        bp: '112/72 mmHg',
        ef: '64%'
      },
      normal: {
        id: 'normal',
        title: 'Normal Rhythm',
        bpm: 74,
        speed: 1.1,
        status: 'Optimal Sinus Rhythm',
        statusColor: '#E52591',
        strokeVol: '78 mL',
        cardiacOutput: '5.2 L/min',
        perfusion: '99.4%',
        bp: '118/76 mmHg',
        ef: '65%'
      },
      active: {
        id: 'active',
        title: 'Active Aerobic',
        bpm: 96,
        speed: 0.85,
        status: 'Active Aerobic Flow',
        statusColor: '#FF66C4',
        strokeVol: '88 mL',
        cardiacOutput: '7.4 L/min',
        perfusion: '99.8%',
        bp: '128/82 mmHg',
        ef: '68%'
      },
      peak: {
        id: 'peak',
        title: 'Peak Perfusion',
        bpm: 120,
        speed: 0.62,
        status: 'Max Hemodynamic Drive',
        statusColor: '#F59E0B',
        strokeVol: '95 mL',
        cardiacOutput: '9.8 L/min',
        perfusion: '99.1%',
        bp: '136/88 mmHg',
        ef: '72%'
      }
    };

    this.initElements();
    this.bindEvents();
    this.applyPreset('normal');
    this.startBpmOscillation();
  }

  initElements() {
    this.heartImg = this.container.querySelector('#cardio-heart-img');
    this.viewport = this.container.querySelector('#cardio-viewport-box');
    this.bpmDisplay = this.container.querySelector('#cardio-bpm-val');
    this.statusBadge = this.container.querySelector('#cardio-status-badge');
    this.statusTitle = this.container.querySelector('#cardio-status-title');
    this.perfusionText = this.container.querySelector('#cardio-perfusion-val');
    this.perfusionBar = this.container.querySelector('#cardio-perfusion-bar');
    this.ekgWave = this.container.querySelector('#cardio-ekg-svg');
    this.pins = this.container.querySelectorAll('.cardio-pin');

    this.presetPills = this.container.querySelectorAll('.cardio-preset-pill');
    this.btnPins = this.container.querySelector('#btn-toggle-pins');
    this.btnEkg = this.container.querySelector('#btn-toggle-ekg');

    this.pinAortaVal = this.container.querySelector('#pin-aorta-val');
    this.pinVentricleVal = this.container.querySelector('#pin-ventricle-val');
  }

  bindEvents() {
    // 1. Preset Pills click
    this.presetPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const pKey = pill.getAttribute('data-preset');
        if (pKey && this.presets[pKey]) {
          this.applyPreset(pKey);
        }
      });
    });

    // 2. Interactive Toggle: Pins
    if (this.btnPins) {
      this.btnPins.addEventListener('click', () => {
        this.isPinsVisible = !this.isPinsVisible;
        this.btnPins.classList.toggle('active', this.isPinsVisible);
        this.pins.forEach(pin => {
          pin.style.display = this.isPinsVisible ? 'flex' : 'none';
        });
      });
    }

    // 3. Interactive Toggle: EKG
    if (this.btnEkg) {
      this.btnEkg.addEventListener('click', () => {
        this.isEkgVisible = !this.isEkgVisible;
        this.btnEkg.classList.toggle('active', this.isEkgVisible);
        if (this.ekgWave) {
          this.ekgWave.style.opacity = this.isEkgVisible ? '0.85' : '0';
        }
      });
    }

    // 4. Interactive 3D Parallax Tilt on Mouse Move
    if (this.viewport && this.heartImg) {
      this.viewport.addEventListener('mousemove', (e) => {
        const rect = this.viewport.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;

        const tiltX = -y * 22; // Degrees
        const tiltY = x * 26;  // Degrees

        this.heartImg.style.transform = `perspective(700px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.04)`;
      });

      this.viewport.addEventListener('mouseleave', () => {
        this.heartImg.style.transform = 'perspective(700px) rotateX(0deg) rotateY(0deg) scale(1)';
      });
    }
  }

  applyPreset(presetKey) {
    const p = this.presets[presetKey];
    if (!p) return;

    this.currentPreset = presetKey;
    this.bpm = p.bpm;
    this.pulseSpeed = p.speed;

    // 1. Update preset pill UI
    this.presetPills.forEach(pill => {
      if (pill.getAttribute('data-preset') === presetKey) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    // 2. Update CSS variable for heartbeat animation speed
    if (this.heartImg) {
      this.heartImg.style.setProperty('--heart-speed', `${p.speed}s`);
    }

    // 3. Update EKG animation speed
    if (this.ekgWave) {
      this.ekgWave.style.setProperty('--ekg-speed', `${(p.speed * 1.5).toFixed(2)}s`);
    }

    // 4. Update Telemetry displays
    if (this.bpmDisplay) {
      this.bpmDisplay.textContent = `${p.bpm} BPM`;
    }
    if (this.statusBadge) {
      this.statusBadge.textContent = p.status;
      this.statusBadge.style.color = p.statusColor;
      this.statusBadge.style.borderColor = p.statusColor;
    }
    if (this.statusTitle) {
      this.statusTitle.textContent = `${p.status} • ${p.cardiacOutput}`;
    }
    if (this.perfusionText) {
      this.perfusionText.textContent = `${p.perfusion} Perfusion`;
      this.perfusionText.style.color = p.statusColor;
    }
    if (this.perfusionBar) {
      this.perfusionBar.style.width = p.perfusion;
      this.perfusionBar.style.background = `linear-gradient(90deg, #812D80, ${p.statusColor})`;
    }

    // 5. Update Pins
    if (this.pinAortaVal) {
      this.pinAortaVal.textContent = p.bp;
    }
    if (this.pinVentricleVal) {
      this.pinVentricleVal.textContent = `EF ${p.ef}`;
    }
  }

  startBpmOscillation() {
    // Subtle real-time heart rate variation (HRV)
    setInterval(() => {
      const jitter = (Math.sin(Date.now() / 1500) * 1.5).toFixed(0);
      const liveBpm = parseInt(this.bpm) + parseInt(jitter);
      if (this.bpmDisplay) {
        this.bpmDisplay.textContent = `${liveBpm} BPM`;
      }
    }, 1200);
  }
}

// Global initialization hook
window.initCardioWorkstation = function(containerId) {
  return new HolographicCardioController(containerId);
};
