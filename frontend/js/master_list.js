import {
    getAllGear, createGear, updateGear, deleteGear, getAllLocations
} from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // Authentication Check
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = 'index.html'; // Redirect to login if not authenticated
        return;
    }

    const gearTableBody = document.getElementById('gearTableBody');
    const addNewItemButton = document.getElementById('addNewItemButton');
    const gearModal = document.getElementById('gearModal');
    const closeModalButton = document.getElementById('closeModalButton');
    const gearForm = document.getElementById('gearForm');
    const modalTitle = document.getElementById('modalTitle');
    const gearIdInput = document.getElementById('gearId');
    const gearLocationSelect = document.getElementById('gearLocation');
    const logoutButton = document.getElementById('logoutButton');
    const errorMessageDiv = document.getElementById('errorMessage');

    let allLocations = []; // To store locations for the dropdown

    // Modified displayError
    function displayError(message, errorObj) {
        let fullMessage = message;
        if (errorObj) { // Check if errorObj is provided
            if (errorObj.data && errorObj.data.detail && Array.isArray(errorObj.data.detail)) {
                const details = errorObj.data.detail.map(e => {
                    let field = e.loc && e.loc.length > 1 ? e.loc[1] : (e.loc && e.loc.length > 0 ? e.loc[0] : 'field');
                    // Make field name more readable if it's like "body.name"
                    field = field.includes('.') ? field.substring(field.lastIndexOf('.') + 1) : field;
                    return `${field.charAt(0).toUpperCase() + field.slice(1)}: ${e.msg}`;
                }).join('; ');
                fullMessage = `Validation Error: ${details}`;
            } else if (errorObj.data && errorObj.data.error && errorObj.data.error.message) {
                fullMessage = errorObj.data.error.message;
                if (errorObj.data.error.details) {
                    fullMessage += ` (${errorObj.data.error.details})`;
                }
            } else if (errorObj.message) { // Fallback to errorObj.message if structure is unexpected
                 fullMessage = errorObj.message;
            }
        }
        errorMessageDiv.textContent = fullMessage;
        errorMessageDiv.classList.remove('hidden');
    }


    function clearError() {
        errorMessageDiv.textContent = '';
        errorMessageDiv.classList.add('hidden');
    }

    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('jwtToken');
        window.location.href = 'index.html';
    });

    const fetchAndDisplayGear = async () => {
        clearError();
        gearTableBody.innerHTML = '<tr><td colspan="9" class="text-center p-4 font-semibold text-sepia">Loading gear... <span class="material-icons animate-spin">refresh</span></td></tr>'; // Loading indicator
        try {
            const gearList = await getAllGear();
            gearTableBody.innerHTML = ''; // Clear existing rows (including loading)

            if (gearList.length === 0) {
                gearTableBody.innerHTML = '<tr><td colspan="9" class="text-center p-4">No gear items found. Try adding some!</td></tr>';
                return;
            }

            gearList.forEach(gear => {
                const row = gearTableBody.insertRow();
                row.className = 'border-t border-sepia bg-opacity-50 hover:bg-sepia-dark hover:bg-opacity-20 transition-colors duration-100';

                const locationName = gear.location ? gear.location.name : 'N/A';

                row.innerHTML = `
                    <td class="px-4 py-3 font-semibold">${gear.name}</td>
                    <td class="px-4 py-3">${gear.description || ''}</td>
                    <td class="px-4 py-3 text-center">${gear.weight} lbs</td>
                    <td class="px-4 py-3 text-center">${gear.cost !== null ? gear.cost.toFixed(2) : 'N/A'}</td>
                    <td class="px-4 py-3 text-center">${gear.value !== null ? gear.value.toFixed(2) : 'N/A'}</td>
                    <td class="px-4 py-3 text-center">
                        <span class="inline-block px-3 py-1 text-xs font-semibold rounded-full
                                     ${gear.legality === 'Legal' ? 'bg-green-200 text-green-800 border border-green-400' :
                                       gear.legality === 'Restricted' ? 'bg-yellow-200 text-yellow-800 border border-yellow-400' :
                                       gear.legality === 'Illegal' ? 'bg-red-200 text-red-800 border border-red-400' : 'bg-gray-200 text-gray-800 border border-gray-400'}">
                            ${gear.legality || 'Unknown'}
                        </span>
                    </td>
                    <td class="px-4 py-3">${gear.category || 'N/A'}</td>
                    <td class="px-4 py-3">${locationName}</td>
                    <td class="px-4 py-3 text-center">
                        <button class="edit-btn p-1 text-sepia hover-sepia transition-colors duration-150" data-id="${gear.id}" title="Edit">
                            <span class="material-icons text-lg">edit</span>
                        </button>
                        <button class="delete-btn p-1 text-red-700 hover:text-red-900 transition-colors duration-150" data-id="${gear.id}" title="Delete">
                            <span class="material-icons text-lg">delete</span>
                        </button>
                    </td>
                `;
            });
            addEventListenersToButtons();
        } catch (error) {
            console.error('Failed to fetch gear:', error);
            // Use the enhanced displayError
            displayError('Could not load gear data.', error);
            gearTableBody.innerHTML = `<tr><td colspan="9" class="text-center p-4 text-red-500">Error loading gear.</td></tr>`;
        }
    };

    const fetchLocations = async () => {
        try {
            allLocations = await getAllLocations();
            gearLocationSelect.innerHTML = '<option value="">-- Select Location --</option>'; // Clear and add default
            allLocations.forEach(loc => {
                const option = document.createElement('option');
                option.value = loc.id;
                option.textContent = `${loc.name} (${loc.type})`;
                gearLocationSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to fetch locations:', error);
            displayError(error.message || 'Could not load locations for the form.');
        }
    };

    function addEventListenersToButtons() {
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', handleEditItem);
        });
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', handleDeleteItem);
        });
    }

    function openModalForCreate() {
        clearError();
        modalTitle.textContent = 'Add New Item';
        gearForm.reset();
        gearIdInput.value = ''; // Ensure ID is cleared for creation
        gearLocationSelect.value = ''; // Reset location dropdown
        gearModal.style.display = 'block';
            gearForm.name.focus(); // Focus the name input
    }

    async function openModalForEdit(gearId) {
        clearError();
        try {
            const gearItem = await getGearById(gearId);
            if (!gearItem) {
                displayError("Could not fetch item details for editing.", {message: "Item not found or error fetching."} ); // Pass simple error obj
                return;
            }
            modalTitle.textContent = 'Edit Item';
            gearForm.reset(); // Reset form first

            gearIdInput.value = gearItem.id;
            gearForm.name.value = gearItem.name;
            gearForm.description.value = gearItem.description || '';
            gearForm.weight.value = gearItem.weight;
            gearForm.cost.value = gearItem.cost !== null ? gearItem.cost : '';
            gearForm.value.value = gearItem.value !== null ? gearItem.value : '';
            gearForm.legality.value = gearItem.legality || '';
            gearForm.category.value = gearItem.category || '';
            gearLocationSelect.value = gearItem.location_id || '';

            gearModal.style.display = 'block';
            gearForm.name.focus(); // Focus the name input
        } catch (error) {
            console.error('Failed to open edit modal:', error);
            displayError('Could not load item data for editing.', error);
        }
    }

    function closeModal() {
        gearModal.style.display = 'none';
        gearForm.reset();
        clearError();
    }

    addNewItemButton.addEventListener('click', openModalForCreate);
    closeModalButton.addEventListener('click', closeModal);
    window.addEventListener('click', (event) => { // Close modal if clicked outside
        if (event.target === gearModal) {
            closeModal();
        }
    });

    gearForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError();
        const id = gearIdInput.value;
        const formData = new FormData(gearForm);
        const gearData = {};
        // Convert FormData to an object, handling potential empty strings for optional numbers
        for (let [key, value] of formData.entries()) {
            if (key === 'id') continue; // Handled separately
            if (value.trim() === '' && (key === 'cost' || key === 'value' || key === 'location_id')) {
                gearData[key] = null; // Send null for optional empty fields
            } else if (key === 'weight' || key === 'cost' || key === 'value') {
                gearData[key] = parseFloat(value);
            } else if (key === 'location_id') {
                gearData[key] = value ? parseInt(value) : null;
            }
            else {
                gearData[key] = value.trim() === '' ? null : value;
            }
        }
        // Ensure required fields are present
        if (!gearData.name || gearData.weight === null || gearData.weight === undefined || isNaN(gearData.weight)) {
            displayError("Name and Weight are required.");
            return;
        }


        try {
            if (id) { // Update existing item
                await updateGear(id, gearData);
            } else { // Create new item
                await createGear(gearData);
            }
            closeModal();
            fetchAndDisplayGear(); // Refresh the list
        } catch (error) {
            console.error('Failed to save gear:', error);
            displayError('Failed to save item.', error); // Pass the full error object
        }
    });

    async function handleEditItem(event) {
        const gearId = event.currentTarget.dataset.id;
        await openModalForEdit(gearId);
    }

    async function handleDeleteItem(event) {
        const gearId = event.currentTarget.dataset.id;
        if (confirm('Are you sure you want to delete this item?')) {
            clearError();
            try {
                await deleteGear(gearId);
                fetchAndDisplayGear(); // Refresh the list
            } catch (error) {
                console.error('Failed to delete gear:', error);
                displayError('Failed to delete item.', error); // Pass the full error object
            }
        }
    }

    // Initial data load
    fetchLocations(); // Load locations for the modal first
    fetchAndDisplayGear(); // Then load gear
});
