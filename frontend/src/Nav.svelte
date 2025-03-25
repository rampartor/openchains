<script>
  import { auth, logout } from './auth.js';

  // Get the current path
  const currentPath = window.location.pathname;

  function handleLogout() {
    logout();
    window.location.href = '/';
  }
</script>

<nav>
  <div class="nav-links">
    {#if !$auth.isAuthenticated}
      <a href="/" class:active={currentPath === '/'}>Login</a>
    {:else}
      {#if $auth.isAdmin}
        <a href="/generator" class:active={currentPath === '/generator'}>Generator</a>
      {/if}
      <button on:click={handleLogout} class="logout-btn">Logout</button>
      <span class="user-info">
        Logged in as: <strong>{$auth.user?.username || 'User'}</strong>
        {#if $auth.isAdmin}
          <span class="admin-badge">Admin</span>
        {/if}
      </span>
    {/if}
  </div>
</nav>

<style>
  nav {
    background-color: #222;
    padding: 1rem;
    margin-bottom: 2rem;
  }

  .nav-links {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2rem;
  }

  a {
    color: #aaa;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
    padding: 0.5rem 1rem;
    border-radius: 4px;
  }

  a:hover {
    color: #fff;
    background-color: #333;
  }

  .active {
    color: #fff;
    background-color: #4a56e2;
  }

  .active:hover {
    background-color: #3a46d2;
  }

  .logout-btn {
    background-color: #e53935;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .logout-btn:hover {
    background-color: #c62828;
  }

  .user-info {
    color: #aaa;
    margin-left: 1rem;
    font-size: 0.9rem;
  }

  .admin-badge {
    background-color: #4a56e2;
    color: white;
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 10px;
    margin-left: 0.5rem;
    font-weight: bold;
  }
</style>
