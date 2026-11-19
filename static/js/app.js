/**
 * HepatoVision AI - Clinical Radiology Portal Client App
 * Pure Vanilla JavaScript (No frameworks required)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const form = document.getElementById('diagnostic-form');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const dropzonePrompt = document.getElementById('dropzone-prompt');
  const filePreviewTag = document.getElementById('file-preview-tag');
  const previewFilename = document.getElementById('preview-filename');
  const btnRemoveFile = document.getElementById('btn-remove-file');
  const selectedSampleInput = document.getElementById('selected_sample');
  const btnAnalyze = document.getElementById('btn-analyze');
  const btnAnalyzeText = document.getElementById('btn-analyze-text');
  const analyzeSpinner = document.getElementById('analyze-spinner');
  const btnResetForm = document.getElementById('btn-reset-form');

  // Console Outputs
  const emptyState = document.getElementById('empty-state');
  const diagnosticView = document.getElementById('diagnostic-view');
  const resClass = document.getElementById('res-class');
  const resRiskBadge = document.getElementById('res-risk-badge');
  const resConfidence = document.getElementById('res-confidence');
  const viewScanImg = document.getElementById('view-scan-img');
  const viewHeatImg = document.getElementById('view-heat-img');
  const blendSlider = document.getElementById('blend-slider');
  const blendVal = document.getElementById('blend-val');
  const probGrid = document.getElementById('prob-grid');
  const resFindings = document.getElementById('res-findings');
  const resRecommendations = document.getElementById('res-recommendations');
  const btnDownloadPdf = document.getElementById('btn-download-pdf');
  const btnOpenVerifyModal = document.getElementById('btn-open-verify-modal');
  const viewerCanvasBox = document.getElementById('viewer-canvas-box');
  const btnInvertView = document.getElementById('btn-invert-view');
  const btnZoomReset = document.getElementById('btn-zoom-reset');

  // History & Modal
  const historyTableBody = document.getElementById('history-table-body');
  const btnRefreshHistory = document.getElementById('btn-refresh-history');
  const verifyModal = document.getElementById('verify-modal');
  const verifyForm = document.getElementById('verify-form');
  const modalRecordId = document.getElementById('modal-record-id');
  const modalDoctorStatus = document.getElementById('modal-doctor-status');
  const modalDoctorNotes = document.getElementById('modal-doctor-notes');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelModal = document.getElementById('btn-cancel-modal');

  let currentRecordId = null;

  // Presets mapping for quick demonstration
  const PRESET_PATIENTS = {
    'sample_normal_liver.png': {
      name: 'Suresh Patel',
      age: 34,
      gender: 'Male',
      symptoms: 'Routine Executive Health Screening (Asymptomatic)',
      alt_ast: 'ALT: 22 U/L, AST: 20 U/L (Normal Reference)'
    },
    'sample_fatty_liver.png': {
      name: 'Meera Verma',
      age: 48,
      gender: 'Female',
      symptoms: 'Mild fatigue, Right Upper Quadrant fullness after meals',
      alt_ast: 'ALT: 64 U/L, AST: 48 U/L (Elevated Transaminases)'
    },
    'sample_cirrhosis_liver.png': {
      name: 'Rajesh Kumar',
      age: 56,
      gender: 'Male',
      symptoms: 'Jaundice, Mild Abdominal Distension (Early Ascites), Chronic Fatigue',
      alt_ast: 'ALT: 110 U/L, AST: 145 U/L (Significant Hepatic Injury)'
    },
    'sample_liver_tumor.png': {
      name: 'Anil Deshmukh',
      age: 62,
      gender: 'Male',
      symptoms: 'Unexplained 8kg weight loss, persistent right hypochondrial dull ache',
      alt_ast: 'ALT: 185 U/L, AST: 210 U/L (Hypervascular Pattern)'
    }
  };

  // =========================================================================
  // 1. Preset Buttons Handler (1-Click Medical Scenarios)
  // =========================================================================
  const presetButtons = document.querySelectorAll('.preset-btn');
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const presetFile = btn.getAttribute('data-preset');
      selectedSampleInput.value = presetFile;

      // Clear any manual file upload
      fileInput.value = '';
      dropzonePrompt.classList.add('hidden');
      filePreviewTag.classList.remove('hidden');
      previewFilename.textContent = `Preset: ${presetFile}`;

      // Auto-fill clinical demographics
      const patient = PRESET_PATIENTS[presetFile];
      if (patient) {
        document.getElementById('patient_name').value = patient.name;
        document.getElementById('age').value = patient.age;
        document.getElementById('gender').value = patient.gender;
        document.getElementById('symptoms').value = patient.symptoms;
        document.getElementById('alt_ast').value = patient.alt_ast;
      }

      showToast(`Loaded ${btn.textContent.trim()} clinical scenario. Click 'Run Diagnostic' to analyze.`, 'info');
    });
  });

  // =========================================================================
  // 2. Dropzone & File Upload Logic
  // =========================================================================
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    // Clear preset selection
    presetButtons.forEach(b => b.classList.remove('active'));
    selectedSampleInput.value = '';

    dropzonePrompt.classList.add('hidden');
    filePreviewTag.classList.remove('hidden');
    previewFilename.textContent = file.name;
    showToast(`Scan file selected: ${file.name}`, 'info');
  }

  btnRemoveFile.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFileSelection();
  });

  function clearFileSelection() {
    fileInput.value = '';
    selectedSampleInput.value = '';
    presetButtons.forEach(b => b.classList.remove('active'));
    filePreviewTag.classList.add('hidden');
    dropzonePrompt.classList.remove('hidden');
  }

  btnResetForm.addEventListener('click', () => {
    form.reset();
    clearFileSelection();
    showToast('Form reset to defaults.', 'info');
  });

  // =========================================================================
  // 3. Deep Learning & Grad-CAM Analysis Submission
  // =========================================================================
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const hasFile = fileInput.files && fileInput.files.length > 0;
    const hasPreset = selectedSampleInput.value !== '';

    if (!hasFile && !hasPreset) {
      showToast('Please upload a medical scan or select a Quick Demonstration Preset.', 'error');
      return;
    }

    // Set UI to loading state
    btnAnalyze.disabled = true;
    btnAnalyzeText.textContent = 'Running DenseNet-121 & Computing Grad-CAM...';
    analyzeSpinner.classList.remove('hidden');

    try {
      const formData = new FormData(form);

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Analysis failed on server.');
      }

      const data = await response.json();
      renderDiagnosticResults(data);
      loadHistory();
      showToast('Diagnostic inference and Grad-CAM generated successfully!', 'success');

    } catch (error) {
      console.error(error);
      showToast(error.message || 'Error running deep learning inference.', 'error');
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = 'Run Deep Learning Diagnostic & Grad-CAM';
      analyzeSpinner.classList.add('hidden');
    }
  });

  // =========================================================================
  // 4. Render AI Diagnostic Results
  // =========================================================================
  function renderDiagnosticResults(data) {
    currentRecordId = data.record_id;

    // Switch view
    emptyState.classList.add('hidden');
    diagnosticView.classList.remove('hidden');

    // Primary outcome
    resClass.textContent = data.predicted_class;
    resConfidence.textContent = `${data.confidence}%`;
    resRiskBadge.textContent = data.risk_level;
    resRiskBadge.style.backgroundColor = data.badge_color;

    // Set Images (Add timestamp to bust browser caching)
    const cacheBuster = `?t=${Date.now()}`;
    viewScanImg.src = data.scan_url + cacheBuster;
    viewHeatImg.src = data.heatmap_url + cacheBuster;

    // Reset slider
    blendSlider.value = 70;
    blendVal.textContent = '70%';
    viewHeatImg.style.opacity = '0.70';

    // Probability bars
    probGrid.innerHTML = '';
    for (const [clsName, probVal] of Object.entries(data.probabilities)) {
      const isSelected = clsName === data.predicted_class;
      const card = document.createElement('div');
      card.className = 'prob-card';
      card.innerHTML = `
        <div class="prob-info">
          <span class="prob-name" style="${isSelected ? 'color: var(--accent-cyan); font-weight:700;' : ''}">${clsName}</span>
          <span class="prob-num">${probVal}%</span>
        </div>
        <div class="prob-bar-track">
          <div class="prob-bar-fill" style="width: ${probVal}%; ${isSelected ? 'background: linear-gradient(90deg, #0284c7, #10b981);' : ''}"></div>
        </div>
      `;
      probGrid.appendChild(card);
    }

    // Findings & Recommendations
    resFindings.textContent = data.findings;
    
    resRecommendations.innerHTML = '';
    const recs = data.recommendations.split('\n');
    recs.forEach(r => {
      if (r.trim()) {
        const item = document.createElement('div');
        item.textContent = `• ${r.trim()}`;
        resRecommendations.appendChild(item);
      }
    });

    // Report PDF link
    btnDownloadPdf.href = data.report_url;

    // Smooth scroll to results
    diagnosticView.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // =========================================================================
  // 5. Interactive Heatmap Blend Slider & Radiology View Controls
  // =========================================================================
  blendSlider.addEventListener('input', () => {
    const val = blendSlider.value;
    blendVal.textContent = `${val}%`;
    viewHeatImg.style.opacity = (val / 100).toString();
  });

  btnInvertView.addEventListener('click', () => {
    viewerCanvasBox.classList.toggle('inverted');
  });

  btnZoomReset.addEventListener('click', () => {
    viewerCanvasBox.classList.remove('inverted');
    blendSlider.value = 70;
    blendVal.textContent = '70%';
    viewHeatImg.style.opacity = '0.70';
  });

  // =========================================================================
  // 6. Patient Diagnostic Records History Table
  // =========================================================================
  async function loadHistory() {
    try {
      const response = await fetch('/api/history');
      if (!response.ok) return;

      const records = await response.json();
      historyTableBody.innerHTML = '';

      if (records.length === 0) {
        historyTableBody.innerHTML = `<tr><td colspan="10" class="text-center">No diagnostic records found yet.</td></tr>`;
        return;
      }

      records.forEach(r => {
        const tr = document.createElement('tr');
        
        // Risk level class
        let pillClass = 'low';
        if (r.risk_level.includes('MODERATE')) pillClass = 'mod';
        else if (r.risk_level.includes('HIGH')) pillClass = 'high';
        else if (r.risk_level.includes('CRITICAL')) pillClass = 'crit';

        tr.innerHTML = `
          <td>${r.created_at}</td>
          <td><strong>${r.patient_id}</strong></td>
          <td>${r.patient_name}</td>
          <td>${r.age} / ${r.gender ? r.gender[0] : 'M'}</td>
          <td>
            <img class="thumb-preview" src="${r.heatmap_url}" alt="Thumbnail">
          </td>
          <td><strong>${r.predicted_class}</strong></td>
          <td>${r.confidence}%</td>
          <td><span class="status-pill ${pillClass}">${r.risk_level}</span></td>
          <td><font size="1" color="#94a3b8">${r.doctor_status}</font></td>
          <td>
            <a href="/api/report/${r.id}" target="_blank" class="btn-mini">
              PDF
            </a>
          </td>
        `;
        historyTableBody.appendChild(tr);
      });
    } catch (err) {
      console.error('Error fetching records:', err);
    }
  }

  btnRefreshHistory.addEventListener('click', () => {
    loadHistory();
    showToast('Records refreshed.', 'info');
  });

  // =========================================================================
  // 7. Radiologist Verification & Sign-off Modal
  // =========================================================================
  btnOpenVerifyModal.addEventListener('click', () => {
    if (!currentRecordId) {
      showToast('Please run an analysis first.', 'error');
      return;
    }
    modalRecordId.value = currentRecordId;
    verifyModal.classList.remove('hidden');
  });

  btnCloseModal.addEventListener('click', () => verifyModal.classList.add('hidden'));
  btnCancelModal.addEventListener('click', () => verifyModal.classList.add('hidden'));

  verifyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const recordId = modalRecordId.value;
    const formData = new FormData();
    formData.append('doctor_status', modalDoctorStatus.value);
    formData.append('doctor_notes', modalDoctorNotes.value);

    try {
      const response = await fetch(`/api/verify/${recordId}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Failed to update verification.');

      verifyModal.classList.add('hidden');
      loadHistory();
      showToast('Radiologist review and signature recorded successfully!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // =========================================================================
  // 8. Toast Helper
  // =========================================================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // QR Modal Elements
  const btnOpenQrModal = document.getElementById('btn-open-qr-modal');
  const qrModal = document.getElementById('qr-modal');
  const btnCloseQrModal = document.getElementById('btn-close-qr-modal');
  const btnCopyUrl = document.getElementById('btn-copy-url');
  const mobileUrlInput = document.getElementById('mobile-url-input');
  const mobileQrImg = document.getElementById('mobile-qr-img');

  // Load Network Info for Mobile Access
  async function loadNetworkInfo() {
    try {
      const res = await fetch('/api/network-info');
      if (res.ok) {
        const netData = await res.json();
        if (mobileUrlInput) mobileUrlInput.value = netData.mobile_url;
        if (mobileQrImg) mobileQrImg.src = `${netData.qr_code_url}?t=${Date.now()}`;
      }
    } catch (err) {
      console.warn('Network info error:', err);
    }
  }

  if (btnOpenQrModal && qrModal) {
    btnOpenQrModal.addEventListener('click', () => {
      loadNetworkInfo();
      qrModal.classList.remove('hidden');
    });
  }

  if (btnCloseQrModal && qrModal) {
    btnCloseQrModal.addEventListener('click', () => {
      qrModal.classList.add('hidden');
    });
  }

  if (btnCopyUrl && mobileUrlInput) {
    btnCopyUrl.addEventListener('click', () => {
      mobileUrlInput.select();
      navigator.clipboard.writeText(mobileUrlInput.value).then(() => {
        showToast('Mobile link copied to clipboard!', 'success');
      }).catch(() => {
        showToast('Link: ' + mobileUrlInput.value, 'info');
      });
    });
  }

  // Initial Load
  loadHistory();
  loadNetworkInfo();
});
