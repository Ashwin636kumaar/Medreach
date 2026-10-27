
const appState = {
  currentScreen: 'LOGIN',
  scannerTarget: 'center', // 'center' | 'patient'
  selectedPatientId: 'TK-209312',
  scannedRefNumber: 'RAM1001',
  patientScannedBarcode: '',
  webcamStream: null,
  activeTab: 'pending',
  tasks: [],
  selectedTask: null,
  paymentAmount: 988.0,
  paymentMethod: 'Cash',
  isExpandedCollection: false
};

document.addEventListener('DOMContentLoaded', () => {
  updateStatusClock();
  setInterval(updateStatusClock, 10000);
  fetchTasks();
});

function updateStatusClock() {
  const clockEl = document.getElementById('liveClockText');
  if (clockEl) {
    const d = new Date();
    const h = d.getHours().toString().padStart(2, '0');
    const m = d.getMinutes().toString().padStart(2, '0');
    clockEl.textContent = `${h}:${m}`;
  }
}


function navigateScreen(screenName) {
  appState.currentScreen = screenName;

 
  const allScreens = document.querySelectorAll('.screen');
  allScreens.forEach(s => s.classList.remove('active'));

  const target = document.getElementById(`screen-${screenName.toLowerCase()}`);
  if (target) {
    target.classList.add('active');
  }


  const statusBar = document.getElementById('mainStatusBar');
  if (screenName === 'BARCODE_SCANNER') {
    statusBar.classList.add('status-bar-dark');
    startCameraScanner();
  } else {
    statusBar.classList.remove('status-bar-dark');
    stopCameraScanner();
  }


  const container = document.getElementById('appScreenContainer');
  if (container) container.scrollTop = 0;
}

function handleLogin(event) {
  if (event) event.preventDefault();
  const ident = document.getElementById('loginIdentifier').value.trim();
  const pass = document.getElementById('loginPassword').value;

  if (!ident) {
    alert('Please enter your mobile number or email ID');
    return;
  }
  if (!pass || pass.length < 4) {
    alert('Please enter your password');
    return;
  }

  
  navigateScreen('HOME');
}


async function fetchTasks() {
  try {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    if (data.success && data.tasks) {
      appState.tasks =SAMPLE_TASKS;
      renderTasksList(appState.activeTab);
    }
  } catch (err) {
    console.warn('Backend fetch note, using cached state:', err);
  }
}

function switchHomeTab(tab) {
  appState.activeTab = tab;
  document.getElementById('tabBtnPending').classList.toggle('active', tab === 'pending');
  document.getElementById('tabBtnCompleted').classList.toggle('active', tab === 'completed');
  renderTasksList(tab);
}

function renderTasksList(tab) {
  const container = document.getElementById('homeTasksContainer');
  container.innerHTML = '';

  const filtered = appState.tasks.filter(t => {
    const status = (t.status || '').toLowerCase().trim();

    if (tab === 'pending') {
        return status === 'pending';
    }

    if (tab === 'completed') {
        return status === 'completed';
    }

    return false;
});

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: #94A3B8; padding: 30px; font-size: 13px;">
        No ${tab} collections found.
      </div>
    `;
    return;
  }

  filtered.forEach(task => {
    const card = document.createElement('div');
    card.className = 'patient-card-item';
    card.innerHTML = `
      <div class="patient-card-top">
        <div class="patient-avatar-title" onclick="openPatientDetail('${task.id}')" style="cursor: pointer;">
          <div class="patient-avatar-round-blue">👤</div>
          <div>
            <div class="patient-fullname">${task.patientName}</div>
            <div class="patient-address-line">${task.address}</div>
          </div>
        </div>
        <button class="patient-phone-btn" onclick="alert('Calling patient: ${task.patientPhone}')">📞</button>
      </div>

      <div class="patient-meta-tags-row">
        <span>🕒 ${task.scheduledTime}</span>
        <span>•</span>
        <span>📍 ${task.distanceKm}km</span>
        <span>•</span>
        <span class="paid-tag-green">${(task.paymentStatus || 'PAID').toUpperCase()}</span>
        ${task.barcode ? `<span style="background: #E2E8F0; padding: 2px 6px; border-radius: 6px; font-weight: 700; font-size: 10px;">🏷️ ${task.barcode}</span>` : ''}
      </div>

      <div class="patient-actions-two-btn">
        <button class="btn-card-cancel-outline" onclick="openRejectReassign('${task.id}')">✕ Cancel</button>
        <button class="btn-card-navigate-fill" onclick="openPatientDetail('${task.id}')">
          ${task.status === 'completed' ? 'View Details' : 'Navigate ➔'}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function handleHomeSearch(query) {
  const q = query.toLowerCase().trim();
  const filtered = appState.tasks.filter(t => 
    t.patientName.toLowerCase().includes(q) || 
    t.address.toLowerCase().includes(q) ||
    (t.referenceNumber && t.referenceNumber.toLowerCase().includes(q))
  );

  const container = document.getElementById('homeTasksContainer');
  container.innerHTML = '';
  filtered.forEach(task => {
    const card = document.createElement('div');
    card.className = 'patient-card-item';
    card.innerHTML = `
      <div class="patient-card-top">
        <div class="patient-avatar-title" onclick="openPatientDetail('${task.id}')" style="cursor: pointer;">
          <div class="patient-avatar-round-blue">👤</div>
          <div>
            <div class="patient-fullname">${task.patientName}</div>
            <div class="patient-address-line">${task.address}</div>
          </div>
        </div>
      </div>
      <div class="patient-actions-two-btn" style="margin-top: 10px;">
        <button class="btn-card-navigate-fill" onclick="openPatientDetail('${task.id}')">Open Task</button>
      </div>
    `;
    container.appendChild(card);
  });
}

function toggleCollectionExpand() {
  appState.isExpandedCollection = !appState.isExpandedCollection;
  const expandedBox = document.getElementById('expandedTubeBox');
  const normalBox = document.getElementById('normalTubeBox');
  if (appState.isExpandedCollection) {
    expandedBox.style.display = 'block';
    normalBox.style.display = 'none';
  } else {
    expandedBox.style.display = 'none';
    normalBox.style.display = 'flex';
  }
}


async function openPatientDetail(taskId) {
  appState.selectedPatientId = taskId;
  let task = appState.tasks.find(t => t.id === taskId);
  
  if (!task) {
    try {
      const res = await fetch(`/api/tasks/${taskId}`);
      const data = await res.json();
      if (data.success) task = data.task;
    } catch (_) {}
  }

  if (task) {
    appState.selectedTask = task;
    document.getElementById('detailName').textContent = task.patientName;
    document.getElementById('detailAddress').textContent = task.address;
    document.getElementById('detailDemographics').textContent = `${task.patientAge} Yrs • ${task.patientGender} • ${task.patientPhone}`;
    document.getElementById('patientBarcodeField').value = task.barcode || appState.patientScannedBarcode || '';

    // Render Test Groups
    const groupContainer = document.getElementById('detailGroupsContainer');
    groupContainer.innerHTML = '';

    if (task.testGroups && task.testGroups.length > 0) {
      task.testGroups.forEach(g => {
        const item = document.createElement('div');
        item.className = 'test-group-card';
        const isSerum = g.tubeType.toLowerCase().includes('serum');
        item.innerHTML = `
          <div class="test-group-top">
            <span class="test-group-title">${g.title}</span>
            <span class="test-group-tube-badge" style="background: ${isSerum ? '#FEE2E2' : '#EDE9FE'}; color: ${isSerum ? '#DC2626' : '#7C3AED'};">
              ${g.tubeType}
            </span>
          </div>
          <div class="test-group-items-list">
            ${g.tests ? g.tests.map(t => t.name).join(' • ') : 'Standard diagnostic assay'}
          </div>
        `;
        groupContainer.appendChild(item);
      });
    } else {
      groupContainer.innerHTML = `
        <div class="test-group-card">
          <div class="test-group-top">
            <span class="test-group-title">Complete Blood Count (CBC)</span>
            <span class="test-group-tube-badge" style="background: #EDE9FE; color: #7C3AED;">EDTA - Lavender</span>
          </div>
          <div class="test-group-items-list">Hemoglobin • RBC Count • Platelet Count • WBC Differential</div>
        </div>
        <div class="test-group-card">
          <div class="test-group-top">
            <span class="test-group-title">Lipid Profile & Glucose</span>
            <span class="test-group-tube-badge" style="background: #FEE2E2; color: #DC2626;">Serum - Red Top</span>
          </div>
          <div class="test-group-items-list">Total Cholesterol • Triglycerides • Fasting Blood Sugar</div>
        </div>
      `;
    }
  }

  navigateScreen('PATIENT_DETAIL');
}


function openRejectReassign(taskId) {
  appState.selectedPatientId = taskId;
  navigateScreen('REJECT_REASSIGN');
}

function submitTaskRejection() {
  const radios = document.getElementsByName('rejectReason');
  let reason = 'Patient not available at home';
  for (let r of radios) {
    if (r.checked) {
      reason = r.value;
      break;
    }
  }
  alert(`Task Rejected: "${reason}". Removed from active queue.`);
  navigateScreen('HOME');
}


function proceedToPaymentScreen() {
  navigateScreen('COLLECT_PAYMENT');
}

function completePayment(method) {
  appState.paymentMethod = method;
  document.getElementById('successPaymentMethodText').textContent = `Received via ${method}`;
  navigateScreen('PAYMENT_SUCCESS');
}


function handleFetchBatchsheetCode() {
  const inputEl = document.getElementById('inputBatchsheetBarcode');
  let code = inputEl.value.trim();
  if (!code) {
    code = 'BS-883921';
    inputEl.value = code;
  }

 
  document.getElementById('inputExpectedContainers').value = '4';
  const helper = document.getElementById('limsHelperText');
  helper.innerHTML = `
    <span style="color: #0D9488; font-weight: 700;">✓ LIMS Verified:</span> Expected 4 sample vials from Indiranagar Clinic.
  `;
}

function saveCenterCollection() {
  const batch = document.getElementById('inputBatchsheetBarcode').value.trim();
  if (!batch) {
    alert('Please enter or fetch batchsheet barcode first!');
    return;
  }
  alert('Center Collection Details successfully saved to LIMS!');
  navigateScreen('HOME');
}


function openScanner(target) {
  appState.scannerTarget = target;
  document.getElementById('scannerBadgeCode').textContent = 'Align barcode in frame...';
  const btn = document.getElementById('btnScannerAction');
  btn.disabled = true;
  btn.textContent = target === 'patient' ? 'Associate Reference' : 'Fetch Reference No';
  navigateScreen('BARCODE_SCANNER');
}

async function startCameraScanner() {
  const video = document.getElementById('scannerVideo');
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false
      });
      appState.webcamStream = stream;
      video.srcObject = stream;
      video.play();
    } catch (err) {
      console.warn('Camera sensor in use or not available on desktop, simulated scanner active:', err);
    }
  }
}

function stopCameraScanner() {
  if (appState.webcamStream) {
    appState.webcamStream.getTracks().forEach(track => track.stop());
    appState.webcamStream = null;
  }
}

function simulateScanDetection() {
  const code = '39' + Math.floor(10000000000000000 + Math.random() * 90000000000000000);
  document.getElementById('scannerBadgeCode').textContent = code;
  const btn = document.getElementById('btnScannerAction');
  btn.disabled = false;
  btn.setAttribute('data-scanned', code);
}

function confirmScannedBarcode() {
  const code = document.getElementById('btnScannerAction').getAttribute('data-scanned') || '3934201948210948201';
  if (appState.scannerTarget === 'patient') {
    appState.patientScannedBarcode = code;
    document.getElementById('patientBarcodeField').value = code;
    navigateScreen('PATIENT_DETAIL');
  } else {
    appState.scannedRefNumber = code;
    document.getElementById('centerRefNumberInput').value = code;
    navigateScreen('CENTER_COLLECTION');
  }
}
