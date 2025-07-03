const API_BASE_URL = '/api'; // Nginx will proxy this

async function request(endpoint, method = 'GET', body = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('jwtToken');
    if (requiresAuth && token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        if (response.status === 401) { // Unauthorized
            console.warn('Unauthorized request. Clearing token and redirecting to login.');
            localStorage.removeItem('jwtToken');
            if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') { // Avoid redirect loop
                 // Ensure we are not already on a page that could be index.html or its equivalent
                if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
                    window.location.href = '/index.html'; // Adjust if your login page is different
                }
            }
            throw new Error('Unauthorized');
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            console.error('API Error:', response.status, errorData);
            let errorMessage = `Error ${response.status}: ${errorData.message || response.statusText}`;
            if (errorData.detail) { // Pydantic errors often in detail
                 if (Array.isArray(errorData.detail)) {
                    errorMessage += errorData.detail.map(e => `\n- ${e.loc.join('.')} - ${e.msg}`).join('');
                 } else if (typeof errorData.detail === 'string') {
                    errorMessage += `\n- ${errorData.detail}`;
                 } else {
                     errorMessage += `\n- ${JSON.stringify(errorData.detail)}`;
                 }
            } else if (errorData.error && errorData.error.message) { // Custom error structure from app.py
                errorMessage = `Error ${response.status}: ${errorData.error.message}`;
                if (errorData.error.details) {
                    errorMessage += ` (${errorData.error.details})`;
                }
            }

            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = errorData;
            throw error;
        }
        if (response.status === 204 || response.headers.get("content-length") === "0") { // No Content or empty body
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error(`Request failed [${method} ${endpoint}]:`, error);
        // Display error to user
        const errorDisplay = document.getElementById('errorMessage');
        if (errorDisplay) {
            errorDisplay.textContent = error.message;
            errorDisplay.style.display = 'block';
        }
        throw error; // Re-throw to be caught by the caller
    }
}

// User Auth API calls
const loginUser = (credentials) => request('/auth/login', 'POST', credentials, false);
const registerUser = (userData) => request('/auth/register', 'POST', userData, false);

// Gear API calls
const getAllGear = (filters = {}) => {
    const queryParams = new URLSearchParams(filters).toString();
    return request(`/gear${queryParams ? '?' + queryParams : ''}`, 'GET');
};
const createGear = (gearData) => request('/gear', 'POST', gearData);
const getGearById = (id) => request('/gear/' + id, 'GET');
const updateGear = (id, gearData) => request('/gear/' + id, 'PUT', gearData);
const deleteGear = (id) => request('/gear/' + id, 'DELETE');

// Location API calls
const getAllLocations = (filters = {}) => {
    const queryParams = new URLSearchParams(filters).toString();
    return request(`/locations${queryParams ? '?' + queryParams : ''}`, 'GET');
};
const createLocation = (locationData) => request('/locations', 'POST', locationData);
const getLocationById = (id) => request('/locations/' + id, 'GET');
const updateLocation = (id, locationData) => request('/locations/' + id, 'PUT', locationData);
const deleteLocation = (id) => request('/locations/' + id, 'DELETE');
const getItemsInLocation = (id) => request(`/locations/${id}/items`, 'GET');

export {
    loginUser, registerUser,
    getAllGear, createGear, getGearById, updateGear, deleteGear,
    getAllLocations, createLocation, getLocationById, updateLocation, deleteLocation, getItemsInLocation,
    request // Exporting generic request for one-off calls if needed
};
