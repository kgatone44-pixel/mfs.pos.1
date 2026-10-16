let currentTransType = 'cash_out';
let selectedAccountId = null;
let appData = {};

document.addEventListener('DOMContentLoaded', () => {
    loadInitialData();
});

async function loadInitialData() {
    try {
        const res = await fetch('/api/initial_data');
        appData = await res.json();
        renderUI();
    } catch (err) {
        console.error("Error loading data:", err);
    }
}

function renderUI() {
    // 1. Render Shift Status
    const shiftBadge = document.getElementById('shiftBadge');
    const shiftActionBtn = document.getElementById('shiftActionBtn');
    
    if (appData.shift) {
        shiftBadge.innerText = "Open";
        shiftBadge.className = "px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        shiftActionBtn.innerHTML = `<button onclick="submitCloseShift()" class="w-full mt-2 py-2 text-xs font-semibold bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg transition">Shift ပိတ်မည်</button>`;
    } else {
        shiftBadge.innerText = "Closed";
        shiftBadge.className = "px-2 py-0.5 text-[10px] font-semibold rounded-full bg-red-500/10 text-red-400 border border-red-500/20";
        shiftActionBtn.innerHTML = `<button onclick="showOpenShiftModal()" class="w-full mt-2 py-2 text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 rounded-lg transition">Shift စတင်ဖွင့်မည်</button>`;
    }

    // 2. Render Accounts Cards
    const accContainer = document.getElementById('accountCardsContainer');
    accContainer.innerHTML = appData.accounts.map(acc => {
        const isSelected = selectedAccountId === acc.id;
        return `
            <div onclick="selectAccount(${acc.id})" class="cursor-pointer p-4 rounded-xl border transition ${isSelected ? 'bg-slate-900 border-slate-900 text-white shadow-md' : 'bg-white border-slate-200 text-slate-800 hover:border-slate-300'}">
                <p class="text-xs font-bold">${acc.name}</p>
                <p class="text-sm font-extrabold mt-1">${acc.balance.toLocaleString()} MMK</p>
            </div>
        `;
    }).join('');

    // Default select first account if none
    if (!selectedAccountId && appData.accounts.length > 0) {
        selectAccount(appData.accounts[0].id);
    }

    // 3. Render Summaries
    document.getElementById('sumCashIn').innerText = `${appData.summary.cash_in.toLocaleString()} MMK`;
    document.getElementById('sumCashOut').innerText = `${appData.summary.cash_out.toLocaleString()} MMK`;
    document.getElementById('sumCommission').innerText = `${appData.summary.commission.toLocaleString()} MMK`;

    // 4. Render Recent Transactions
    const transList = document.getElementById('recentTransList');
    transList.innerHTML = appData.transactions.map(t => `
        <div class="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between text-xs">
            <div>
                <span class="font-bold ${t.trans_type === 'cash_out' ? 'text-red-600' : 'text-emerald-600'}">${t.trans_type === 'cash_out' ? 'Cash Out' : 'Cash In'}</span>
                <p class="text-slate-500 text-[10px]">${t.account_name}</p>
            </div>
            <div class="text-right">
                <p class="font-bold">${t.amount.toLocaleString()} MMK</p>
                <span class="text-[10px] text-slate-400">${t.created_at.split(' ')[1]}</span>
            </div>
        </div>
    `).join('');
}

function setTransType(type) {
    currentTransType = type;
    const btnOut = document.getElementById('tabCashOut');
    const btnIn = document.getElementById('tabCashIn');

    if (type === 'cash_out') {
        btnOut.className = "flex-1 py-3 font-semibold rounded-xl text-sm transition shadow-sm bg-red-500 text-white";
        btnIn.className = "flex-1 py-3 font-semibold rounded-xl text-sm transition text-slate-600 hover:text-slate-900";
        document.getElementById('inputCommRate').value = appData.settings.default_commission_cash_out || "0.5";
    } else {
        btnIn.className = "flex-1 py-3 font-semibold rounded-xl text-sm transition shadow-sm bg-emerald-500 text-white";
        btnOut.className = "flex-1 py-3 font-semibold rounded-xl text-sm transition text-slate-600 hover:text-slate-900";
        document.getElementById('inputCommRate').value = appData.settings.default_commission_cash_in || "1.0";
    }
    calculateCommission();
}

function selectAccount(id) {
    selectedAccountId = id;
    renderUI();
}

function setQuickAmount(val) {
    document.getElementById('inputAmount').value = val;
    calculateCommission();
}

function calculateCommission() {
    const amt = parseFloat(document.getElementById('inputAmount').value) || 0;
    const rate = parseFloat(document.getElementById('inputCommRate').value) || 0;
    const comm = (amt * rate) / 100;
    document.getElementById('inputCommAmount').value = comm;
    
    // Formatting Amount in words
    document.getElementById('amountWords').innerText = amt > 0 ? `${amt.toLocaleString()} MMK` : '';
}

async function submitTransaction() {
    const amount = parseFloat(document.getElementById('inputAmount').value);
    if (!amount || !selectedAccountId) {
        alert("ကျေးဇူးပြု၍ ပမာဏနှင့် အကောင့် မှန်ကန်စွာ ရွေးချယ်ပါ");
        return;
    }

    const payload = {
        trans_type: currentTransType,
        account_id: selectedAccountId,
        amount: amount,
        commission: parseFloat(document.getElementById('inputCommAmount').value) || 0,
        customer_info: document.getElementById('inputCustomer').value,
        note: document.getElementById('inputNote').value
    };

    const res = await fetch('/api/transaction/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.status === 'success') {
        document.getElementById('inputAmount').value = '';
        document.getElementById('inputCustomer').value = '';
        document.getElementById('inputNote').value = '';
        calculateCommission();
        loadInitialData();
    }
}

// Modal & Drawer controls
function showOpenShiftModal() { document.getElementById('modalOpenShift').classList.remove('hidden'); }
async function submitOpenShift() {
    const cash = parseFloat(document.getElementById('inputOpeningCash').value) || 0;
    await fetch('/api/shift/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opening_cash: cash })
    });
    document.getElementById('modalOpenShift').classList.add('hidden');
    loadInitialData();
}

async function submitCloseShift() {
    const actual = prompt("လက်ရှိ အပြင်ငွေသား (Cash in Hand) စုစုပေါင်း ရိုက်ထည့်ပါ:");
    if (actual !== null) {
        const res = await fetch('/api/shift/close', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ actual_cash: parseFloat(actual) || 0 })
        });
        const result = await res.json();
        alert(`Shift ပိတ်ပြီးပါပြီ။ Discrepancy: ${result.discrepancy} MMK`);
        loadInitialData();
    }
}

function openSettingsDrawer() {
    document.getElementById('settingsDrawer').classList.remove('-translate-x-full');
    document.getElementById('drawerBackdrop').classList.remove('hidden');
}
function closeSettingsDrawer() {
    document.getElementById('settingsDrawer').classList.add('-translate-x-full');
    document.getElementById('drawerBackdrop').classList.add('hidden');
}

function exportCSV() {
    window.location.href = '/api/reports/export_csv';
}