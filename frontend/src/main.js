import { mount } from 'svelte';
import './app.css';
import App from './App.svelte';
import Generator from './Generator.svelte';

// Check auth status from localStorage
function isAuthenticated() {
  return !!localStorage.getItem('token');
}

// Check if user is admin from localStorage (simplified approach)
// This is just for routing - actual authorization happens on the backend
function isAdmin() {
  try {
    // Check for auth info in localStorage
    const userDataStr = localStorage.getItem('userData');
    if (userDataStr) {
      try {
        const userData = JSON.parse(userDataStr);
        return userData.role === 'admin';
      } catch (err) {
        console.error('Error parsing user data:', err);
      }
    }

    // Legacy check for JWT payload (may not be accurate)
    const token = localStorage.getItem('token');
    if (!token) return false;

    return false; // Default to false for security if we can't determine properly
  } catch (e) {
    console.error('Error checking admin status', e);
    return false;
  }
}

// Simple routing
const routes = {
  '/': App,
  '/generator': Generator
};

// Simple authorization
function shouldRedirectToLogin(path) {
  if (path === '/') return false;

  if (!isAuthenticated()) return true;

  // Generator page requires admin privileges
  if (path === '/generator' && !isAdmin()) return true;

  return false;
}

// Get current path or default to '/'
let path = window.location.pathname || '/';

// Redirect if necessary
if (shouldRedirectToLogin(path)) {
  window.location.pathname = '/';
  path = '/';
}

const component = routes[path] || routes['/'];

const app = mount(component, {
  target: document.getElementById('app'),
});

export default app;
