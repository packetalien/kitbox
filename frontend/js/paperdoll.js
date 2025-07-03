import { getAllGear, getAllLocations } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const logoutButton = document.getElementById('logoutButtonPaperdoll');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('jwtToken');
            window.location.href = 'index.html';
        });
    }

    const paperdollContainer = document.getElementById('paperdollContainer');
    const equippedItemsListDiv = document.getElementById('equippedItemsList');
    const containersListDiv = document.getElementById('containersList');
    const errorMessageDiv = document.getElementById('errorMessagePaperdoll');

    const slotDefinitions = [
        { name: 'Head', type: 'Body Slot', style_class: 'slot-Head' },
        { name: 'Neck', type: 'Body Slot', style_class: 'slot-Neck' },
        { name: 'Shoulders', type: 'Body Slot', style_class: 'slot-Shoulders' }, // Generic, if no L/R
        { name: 'Shoulder L', type: 'Body Slot', style_class: 'slot-Shoulder_L' },
        { name: 'Shoulder R', type: 'Body Slot', style_class: 'slot-Shoulder_R' },
        { name: 'Arms', type: 'Body Slot', style_class: 'slot-Arms' }, // Generic
        { name: 'Arms L', type: 'Body Slot', style_class: 'slot-Arms_L' },
        { name: 'Arms R', type: 'Body Slot', style_class: 'slot-Arms_R' },
        { name: 'Hands', type: 'Body Slot', style_class: 'slot-Hands' }, // Generic
        { name: 'Hand L', type: 'Body Slot', style_class: 'slot-Hand_L' },
        { name: 'Hand R', type: 'Body Slot', style_class: 'slot-Hand_R' },
        { name: 'Torso', type: 'Body Slot', style_class: 'slot-Torso' },
        { name: 'Waist', type: 'Body Slot', style_class: 'slot-Waist' },
        { name: 'Legs', type: 'Body Slot', style_class: 'slot-Legs' },
        { name: 'Feet', type: 'Body Slot', style_class: 'slot-Feet' }, // Generic
        { name: 'Foot L', type: 'Body Slot', style_class: 'slot-Foot_L' },
        { name: 'Foot R', type: 'Body Slot', style_class: 'slot-Foot_R' },
        // Add more slots here if your schema supports them and you have CSS for them
        // { name: 'Backpack', type: 'Container', style_class: 'slot-Backpack' } // Example if backpack is a visual slot
    ];


    function displayError(message) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.classList.remove('hidden');
    }

    function clearError() {
        errorMessageDiv.textContent = '';
        errorMessageDiv.classList.add('hidden');
    }

    async function initializePaperdoll() {
        clearError();
        try {
            const [gearItems, locations] = await Promise.all([
                getAllGear(),
                getAllLocations()
            ]);

            // Create visual slots on paperdoll image
            slotDefinitions.forEach(slotDef => {
                // Only create divs for slots that are meant to be visual on the paperdoll
                if (slotDef.style_class && slotDef.type === 'Body Slot') {
                    const slotDiv = document.createElement('div');
                    slotDiv.classList.add('equipment-slot', slotDef.style_class);
                    slotDiv.title = slotDef.name; // Tooltip for slot name
                    slotDiv.dataset.slotName = slotDef.name;
                    slotDiv.textContent = slotDef.name; // Initial text
                    paperdollContainer.appendChild(slotDiv);
                }
            });

            // Populate equipped items
            equippedItemsListDiv.innerHTML = '';
            const bodySlotLocations = locations.filter(loc => loc.type === 'Body Slot');

            bodySlotLocations.forEach(loc => {
                const itemsInSlot = gearItems.filter(item => item.location_id === loc.id);
                const slotP = document.createElement('p');
                slotP.className = 'text-sm mb-1 p-2 rounded container-list-item';

                let itemText = itemsInSlot.length > 0 ? itemsInSlot.map(i => i.name).join(', ') : 'Empty';
                slotP.innerHTML = `<strong class="font-semibold">${loc.name}:</strong> ${itemText}`;
                equippedItemsListDiv.appendChild(slotP);

                // Update visual slot on paperdoll more robustly
                const slotDef = slotDefinitions.find(sd => sd.name === loc.name && sd.type === 'Body Slot');
                if (slotDef && slotDef.style_class) {
                    const visualSlotDiv = paperdollContainer.querySelector(`.${slotDef.style_class}`);
                    if (visualSlotDiv) {
                        if (itemsInSlot.length > 0) {
                            visualSlotDiv.textContent = itemsInSlot[0].name.substring(0, 12) + (itemsInSlot[0].name.length > 12 ? '...' : ''); // Shorten text
                            visualSlotDiv.title = itemsInSlot.map(i => i.name).join(', '); // Full name in tooltip
                        } else {
                            visualSlotDiv.textContent = loc.name; // Show slot name if empty
                            visualSlotDiv.title = loc.name;
                        }
                    }
                } else {
                    // This means a 'Body Slot' location from DB doesn't have a visual definition
                    // console.warn(`No slot definition or style_class for location: ${loc.name}`);
                }
            });
            if (bodySlotLocations.length === 0) {
                equippedItemsListDiv.innerHTML = '<p>No body slots defined or no items equipped.</p>';
            }


            // Populate containers list
            containersListDiv.innerHTML = '';
            const containerLocations = locations.filter(loc => loc.type === 'Container');
            if (containerLocations.length > 0) {
                containerLocations.forEach(container => {
                    const containerLink = document.createElement('a');
                    containerLink.href = `containers.html?location_id=${container.id}&name=${encodeURIComponent(container.name)}`;
                    containerLink.className = 'block p-3 mb-2 rounded-md hover:bg-sepia-light transition-colors duration-150 container-list-item shadow';
                    containerLink.innerHTML = `
                        <strong class="font-semibold text-md">${container.name}</strong>
                        <span class="text-xs block text-gray-600">(Click to view contents)</span>
                    `;
                    containersListDiv.appendChild(containerLink);
                });
            } else {
                containersListDiv.innerHTML = '<p>No containers found.</p>';
            }

        } catch (error) {
            console.error("Error initializing paperdoll:", error);
            displayError(error.message || "Could not load paperdoll data.");
            equippedItemsListDiv.innerHTML = '<p class="text-red-500">Error loading equipped items.</p>';
            containersListDiv.innerHTML = '<p class="text-red-500">Error loading containers.</p>';
        }
    }

    initializePaperdoll();
});
