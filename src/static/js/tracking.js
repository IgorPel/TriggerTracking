console.log("Connecting for user:", currentUserId);
const ws = new WebSocket(`ws://${window.location.host}/ws/${currentUserId}`);

ws.onopen = function() {
    document.getElementById("status").innerHTML = "🟢 Online";
};

const deleteBtns = document.querySelectorAll('.delete');

deleteBtns.forEach(button => {
    button.addEventListener('click', async function(event) {
        const deleteBtn = event.target.closest('tr');
        const row = deleteBtn.closest('tr');
        const rowID = row.id.split('-').pop();

        const confirmed = confirm(`Are you sure want to delete ${rowID} trigger?`)
        if(confirmed) {
            try {
                const response = await fetch(`/delete/${rowID}`, {
                    method: 'DELETE'
                })
                if (response.ok) {
                    console.log("All okay")
                    location.reload()
                } else {
                    console.log("Not okay")
                }
            } catch(error) {
                alert(`Сталася помилка на сервері`);
            }


        }

    })

})



ws.onmessage = function(event) {
    try {
        let data = JSON.parse(event.data);

        if (data.type === "TRIGGER_ACTIVATED") {

            let row = document.getElementById("row-trigger-" + data.trigger_id);

            if (row) {
                row.classList.remove("triggered-row");
                row.classList.remove("de-triggered-row");

                void row.offsetWidth;
                row.classList.add("triggered-row");

                let timeCell = row.querySelector(".last-triggered");
                if (timeCell) {
                    timeCell.innerText = data.timestamp + " (New!)";
                    timeCell.style.fontWeight = "bold";
                }
            }

            let msgDiv = document.getElementById("messages");
            msgDiv.innerHTML = `<div style="border-left: 5px solid red; padding: 5px; background: #eee;">
                🔥 <b>${data.trigger_id}</b> спрацював! ${data.timestamp}
            </div>` + msgDiv.innerHTML;
        }
        else if(data.type === "TRIGGER_DEACTIVATED")
        {
            let row = document.getElementById("row-trigger-" + data.trigger_id);

            if (row) {
                row.classList.remove("triggered-row");
                row.classList.remove("de-triggered-row");
                void row.offsetWidth;
                row.classList.add("de-triggered-row");

                let timeCell = row.querySelector(".last-triggered");
                if (timeCell) {
                    timeCell.innerText = "Was " + data.timestamp;
                    timeCell.style.fontWeight = "bold";
                }
            }

            let msgDiv = document.getElementById("messages");
            msgDiv.innerHTML = `<div style="border-left: 5px solid gray; padding: 5px; background: #eee;">
                💨 <b>${data.trigger_id}</b> вже неактуально! ${data.timestamp}
            </div>` + msgDiv.innerHTML;
        }

    } catch(e) {
        console.log("Not JSON:", event.data);
    }
};