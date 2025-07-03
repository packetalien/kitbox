import { getItemsInLocation, getAllGear, updateGear } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const logoutButton = document.getElementById('logoutButtonContainer');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('jwtToken');
            window.location.href = 'index.html';
        });
    }

    const containerNameTitle = document.getElementById('containerNameTitle');
    const containerPageTitle = document.getElementById('containerPageTitle');
    const itemsTableBody = document.getElementById('containerItemsTableBody');
    const totalWeightEl = document.getElementById('totalWeight');
    const totalValueEl = document.getElementById('totalValue');
    const errorMessageDiv = document.getElementById('errorMessageContainer');

    const addItemToContainerButton = document.getElementById('addItemToContainerButton');
    const addItemModal = document.getElementById('addItemModal');
    const closeAddItemModalButton = document.getElementById('closeAddItemModalButton');
    const itemSearchInput = document.getElementById('itemSearchInput');
    const itemListContainer = document.getElementById('itemListContainer');
    const modalContainerNameSpan = document.getElementById('modalContainerName');
    const addItemModalErrorMessageDiv = document.getElementById('addItemModalErrorMessage');


    let currentContainerId = null;
    let currentContainerName = 'Container';
    let allGearItems = []; // To store all available gear for adding

    function displayError(message, modal = false) {
        const div = modal ? addItemModalErrorMessageDiv : errorMessageDiv;
        div.textContent = message;
        div.classList.remove('hidden');
    }

    function clearError(modal = false) {
        const div = modal ? addItemModalErrorMessageDiv : errorMessageDiv;
        div.textContent = '';
        div.classList.add('hidden');
    }

    const params = new URLSearchParams(window.location.search);
    currentContainerId = params.get('location_id');
    currentContainerName = params.get('name') || 'Container';

    if (containerNameTitle) containerNameTitle.textContent = `${currentContainerName} Contents`;
    if (containerPageTitle) containerPageTitle.textContent = `KitBox - ${currentContainerName}`;
    if (modalContainerNameSpan) modalContainerNameSpan.textContent = currentContainerName;


    async function fetchContainerItems() {
        if (!currentContainerId) {
            displayError("No container ID specified.");
            itemsTableBody.innerHTML = '<tr><td colspan="5" class="text-center p-4">Invalid container selected.</td></tr>';
            return;
        }
        clearError();
        try {
            const items = await getItemsInLocation(currentContainerId);
            itemsTableBody.innerHTML = '';
            let runningTotalWeight = 0;
            let runningTotalValue = 0;

            if (items.length === 0) {
                itemsTableBody.innerHTML = '<tr><td colspan="5" class="text-center p-4">This container is empty.</td></tr>';
            } else {
                items.forEach(item => {
                    const row = itemsTableBody.insertRow();
                    row.className = 'border-t border-sepia bg-opacity-50 hover:bg-sepia-dark hover:bg-opacity-20 transition-colors duration-100';
                    row.innerHTML = `
                        <td class="px-4 py-3 font-semibold">${item.name}</td>
                        <td class="px-4 py-3 text-center">${item.weight} lbs</td>
                        <td class="px-4 py-3 text-center">${item.value !== null ? item.value.toFixed(2) : 'N/A'}</td>
                        <td class="px-4 py-3">${item.category || 'N/A'}</td>
                        <td class="px-4 py-3 text-center">
                            <button class="remove-item-btn p-1 text-orange-600 hover:text-orange-800 transition-colors duration-150" data-item-id="${item.id}" title="Remove from Container">
                                <span class="material-icons text-lg">archive</span>
                            </button>
                        </td>
                    `;
                    runningTotalWeight += item.weight || 0;
                    runningTotalValue += item.value || 0;
                });
            }
            totalWeightEl.textContent = runningTotalWeight.toFixed(2);
            totalValueEl.textContent = runningTotalValue.toFixed(2);
            addRemoveButtonListeners();

        } catch (error) {
            console.error("Error fetching container items:", error);
            displayError(error.message || "Could not load items for this container.");
            itemsTableBody.innerHTML = `<tr><td colspan="5" class="text-center p-4 text-red-500">Error loading items.</td></tr>`;
        }
    }

    async function fetchAllGearForModal() {
        try {
            allGearItems = await getAllGear(); // Fetch all gear
            renderItemListForModal(); // Initial render (might be empty or show all)
        } catch (error) {
            console.error("Error fetching all gear for modal:", error);
            displayError("Could not load gear list for adding.", true);
        }
    }

    function renderItemListForModal(filterText = "") {
        itemListContainer.innerHTML = ''; // Clear previous items
        const filteredItems = allGearItems.filter(item =>
            item.name.toLowerCase().includes(filterText.toLowerCase()) &&
            item.location_id !== parseInt(currentContainerId) // Exclude items already in this container
        );

        if (filteredItems.length === 0) {
            itemListContainer.innerHTML = '<p class="text-gray-500 p-2">No matching items found or all are already in this container.</p>';
            return;
        }

        filteredItems.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-200 text-sm text-gray-800';
            itemDiv.textContent = `${item.name} (W: ${item.weight}, V: ${item.value || 0}) ${item.location ? '- In: '+item.location.name : ''}`;
            itemDiv.dataset.itemId = item.id;
            itemDiv.addEventListener('click', async () => {
                await handleAddItemToContainer(item.id);
            });
            itemListContainer.appendChild(itemDiv);
        });
    }

    itemSearchInput.addEventListener('input', (e) => {
        renderItemListForModal(e.target.value);
    });

    async function handleAddItemToContainer(itemId) {
        clearError(true); // Clear modal error
        try {
            // The item to add needs its location_id updated to currentContainerId
            await updateGear(itemId, { location_id: parseInt(currentContainerId) });
            addItemModal.style.display = 'none'; // Close modal
            fetchContainerItems(); // Refresh items in container
            fetchAllGearForModal(); // Refresh items in modal (as one is now moved)
        } catch (error) {
            console.error("Error adding item to container:", error);
            displayError(error.message || "Failed to add item to container.", true);
        }
    }

    async function handleRemoveItemFromContainer(event) {
        const itemId = event.currentTarget.dataset.itemId;
        if (!itemId) return;

        // For "removing", we'll set location_id to null (unassigned)
        // Could also be a specific "limbo" location if desired.
        if (confirm(`Are you sure you want to remove this item from ${currentContainerName}? It will become unassigned.`)) {
            clearError();
            try {
                await updateGear(itemId, { location_id: null });
                fetchContainerItems(); // Refresh list
                fetchAllGearForModal(); // Refresh items in modal (as one is now available)
            } catch (error) {
                console.error("Error removing item:", error);
                displayError(error.message || "Failed to remove item from container.");
            }
        }
    }

    function addRemoveButtonListeners() {
        document.querySelectorAll('.remove-item-btn').forEach(button => {
            button.addEventListener('click', handleRemoveItemFromContainer);
        });
    }


    if (addItemToContainerButton) {
        addItemToContainerButton.addEventListener('click', () => {
            clearError(true);
            itemSearchInput.value = ''; // Clear search
            fetchAllGearForModal().then(() => { // Ensure gear is loaded before showing
                 renderItemListForModal(); // Render with no filter initially
                 addItemModal.style.display = 'block';
            });
        });
    }
    if (closeAddItemModalButton) {
        closeAddItemModalButton.addEventListener('click', () => addItemModal.style.display = 'none');
    }
    window.addEventListener('click', (event) => {
        if (event.target === addItemModal) {
            addItemModal.style.display = 'none';
        }
    });


    // Initial Load
    if (currentContainerId) {
        fetchContainerItems();
    } else {
        displayError("Container not specified. Please go back to the paperdoll and select a container.");
        itemsTableBody.innerHTML = '<tr><td colspan="5" class="text-center p-4">No container selected.</td></tr>';
    }
});
