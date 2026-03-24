// 1. Змінна, де будемо зберігати список монет
let validCoins = [];


async function fetchCoins() {
    const fallbackCoins = [
        'bitcoin', 'ethereum', 'tether', 'xrp', 'binancecoin',
        'usdc', 'solana', 'tron', 'dogecoin', 'bitcoin cash',
        'cardano', 'unus sed leo', 'hyperliquid', 'canton network',
        'chainlink', 'ethena', 'monero', 'stellar', 'dai', 'zcash',
        'hedera', 'litecoin', 'avalanche', 'paypal usd', 'shiba inu',
        'sui', 'toncoin', 'cronos', 'world liberty financial',
        'polkadot', 'uniswap', 'mantle', 'bittensor', 'aave',
        'pepe', 'astar', 'bitget token', 'kaspa', 'cosmos',
        'internet computer', 'polygon', 'arbitrum', 'optimism',
        'near', 'injective', 'aptos', 'stacks', 'immutable',
        'lido dao', 'okb', 'render', 'the graph', 'vechain', 'thorchain',
        'fantom', 'algorand', 'flow', 'synthetix', 'maker',
        'the sandbox', 'decentraland', 'axie infinity', 'tezos',
        'eos', 'quant', 'gala', 'multiversX', 'theta network',
        'helium', 'pyth network', 'jupiter', 'celestia', 'sei',
        'starknet', 'bonk', 'mog coin', 'worldcoin', 'floki',
        'akash network', 'arweave', 'beam', 'echelon prime',
        'curve dao', 'pancakeswap', 'dydx', 'pendle', 'fetch.ai',
        'singularitynet', 'ioia', 'kava', 'zilliqa', 'jasmyCoin',
        'frax share', 'rocket pool', 'conflux', 'woo network',
        '1inch', 'enjin coin', 'mask network', 'livepeer'
    ]

    validCoins = fallbackCoins;

    // Оновлюємо випадаючий список
    updateDatalist();
}

// 3. Оновлення <datalist id="crypto-list"> в HTML
function updateDatalist() {
    const datalist = document.getElementById('crypto-list');
    datalist.innerHTML = ''; // Очистити старе

    // Додаємо популярні монети на початок, або всі підряд
    validCoins.forEach(coinId => {
        const option = document.createElement('option');
        option.value = coinId;
        datalist.appendChild(option);
    });
}

// 4. Функція перевірки (валідації)
function isCoinValid(coinName) {
    // Переводимо в нижній регістр і шукаємо в масиві
    return validCoins.includes(coinName.toLowerCase().trim());
}

// --- ЗАПУСК ---
fetchCoins(); // Завантажуємо список при старті скрипта


document.getElementById('cancel-btn').addEventListener("click", () => {
    window.location.href = "/tracking/";
})

document.getElementById('rows-container').addEventListener('click', function(e){
    if(e.target.classList.contains('btn-delete')) {
        const row = event.target.closest('.trigger-row'); // Знаходимо батьківський рядок
        row.remove();
    }
})

document.addEventListener('DOMContentLoaded', () => {
    const configElement = document.getElementById('trigger-config');
    const existingTriggerData = JSON.parse(configElement.dataset.triggerData);
    const editTriggerId = configElement.dataset.triggerId;

    const container = document.getElementById('rows-container');
    const template = document.getElementById('row-template');

    // Функція додавання рядка (тепер приймає об'єкт з даними)
    function addRow(initialData = null) {
        const clone = template.content.cloneNode(true);
        const rowDiv = clone.querySelector('.trigger-row');
        // Знаходимо всі поля в новому рядку
        const assetInput = clone.querySelector('.asset');
        const operatorSelect = clone.querySelector('.operator');
        const valueInput = clone.querySelector('.value');
        const logicSelect = clone.querySelector('.boolean-op');
        const deleteBtn = clone.querySelector('.btn-delete');

        // 🔥 Якщо є передані дані (Режим редагування), заповнюємо поля
        if (initialData) {
            assetInput.value = initialData.arg1 || "";
            operatorSelect.value = initialData.operation || "gt";
            valueInput.value = initialData.arg2 || "";
            logicSelect.value = initialData.boolean_operation || "";
        }

        container.appendChild(clone);
    }



    // 🔥 ІНІЦІАЛІЗАЦІЯ: Перевіряємо, чи є дані для редагування
    if (existingTriggerData && existingTriggerData.length > 0) {
        // Якщо редагуємо: створюємо рядок для кожної умови
        existingTriggerData.forEach(condition => {
            addRow(condition);
        });
    } else {
        // Якщо створюємо новий: просто один порожній рядок
        addRow();
    }


    // Слухач кнопки "Додати умову"
    document.getElementById('add-btn').addEventListener('click', () => addRow());

    // Збереження
    document.getElementById('submit-btn').addEventListener('click', async () => {
        const rows = document.querySelectorAll(".trigger-row")
        const data = []

        let HasError = false;

        rows.forEach((row, index, array) => {
            const select_asset = row.querySelector('.asset')
            const asset = select_asset.value

            if (!isCoinValid(asset)) {
                alert(`Помилка: Монети "${asset}" не існує (або ми її не підтримуємо).`);
                select_asset.style.borderColor = "red"; // Підсвітити червоним
                HasError = true;
            } else {
                select_asset.style.borderColor = "#ddd"; // Скинути колір
            }

            const select_value = row.querySelector('.value')
            const value = Number(select_value.value)


            if (!Number.isInteger(value)) {
                alert(`Помилка: приймається виключно натульні числа`);
                select_value.style.borderColor = "red"; // Підсвітити червоним
                HasError = true;
            } else {
                select_value.style.borderColor = "#ddd";
            }


            const NextRow = array[index + 1];
            const select_boolean_op = row.querySelector('.boolean-op')
            if(NextRow && select_boolean_op.value == '') {
                alert(`Помилка: між рядками "${index}" та "${index+1}" немає булевої операції`);
                select_boolean_op.style.borderColor = "red"; // Підсвітити червоним
                HasError = true;
            } else {
                select_value.style.borderColor = "#ddd";
            }

            if(!HasError) {
                const rowData = {
                    arg1: asset,
                    operation: row.querySelector('.operator').value,
                    arg2: select_value.value,
                    boolean_operation: select_boolean_op.value
                }
                data.push(rowData)
            }
        })

        if (!HasError) {
            const payload = { items: data };

            // Визначаємо куди відправляти (Створення чи Оновлення)
            const isEditing = editTriggerId && editTriggerId !== "null";

            const url = isEditing ? `/edit/${editTriggerId}` : '/add_trigger';
            const method = isEditing ? 'PUT' : 'POST'; // або POST для обох, як тобі зручніше



            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    window.location.href = "/tracking/";
                } else {
                    // Якщо сервер поверне 422, ви побачите це тут
                    const errorDetail = await response.json();
                    console.log("Деталі помилки:", errorDetail);
                    alert(`Помилка валідації: ${JSON.stringify(errorDetail.detail)}`);
                }
            } catch (error) {
                alert(`Сталася помилка на сервері`);
            }
        }
    });
});
