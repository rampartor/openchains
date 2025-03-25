<script>
  import Nav from './Nav.svelte';
  import { auth, fetchUserInfo } from './auth.js';
  import { onMount } from 'svelte';

  let userCount = 10;
  let slipCount = 20;
  let message = '';
  let loading = false;
  let results = null;
  let error = null;

  onMount(() => {
    // Verify user is logged in and is admin
    fetchUserInfo();
  });

  async function handleGenerate() {
    loading = true;
    message = '';
    error = null;
    results = null;

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ user_count: userCount, slip_count: slipCount }),
      });

      const data = await response.json();

      if (response.ok) {
        results = data;
        message = data.message;
      } else {
        error = data.detail || 'Error generating data';

        // If unauthorized, redirect to login
        if (response.status === 401 || response.status === 403) {
          window.location.href = '/';
        }
      }
    } catch (err) {
      console.error('Generator error:', err);
      error = 'Network error or server unreachable';
    } finally {
      loading = false;
    }
  }
</script>

<div>
  <Nav />
  <main>
  <h1>Data Generator</h1>
  <p class="description">Generate random users and transaction slips for testing</p>

  <form on:submit|preventDefault={handleGenerate}>
    <div class="form-group">
      <label for="userCount">Number of Users:</label>
      <input
        id="userCount"
        type="number"
        bind:value={userCount}
        min="1"
        max="1000"
        required
      />
      <span class="hint">Max: 1000</span>
    </div>

    <div class="form-group">
      <label for="slipCount">Number of Slips:</label>
      <input
        id="slipCount"
        type="number"
        bind:value={slipCount}
        min="1"
        max="5000"
        required
      />
      <span class="hint">Max: 5000</span>
    </div>

    <button type="submit" disabled={loading}>
      {loading ? 'Generating...' : 'Generate Data'}
    </button>
  </form>

  {#if error}
    <div class="message error">
      {error}
    </div>
  {/if}

  {#if results}
    <div class="results">
      <h2>Generation Results</h2>
      <div class="stats">
        <div class="stat-item">
          <span class="stat-label">Users Created:</span>
          <span class="stat-value">{results.users_created}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Slips Created:</span>
          <span class="stat-value">{results.slips_created}</span>
        </div>
      </div>
      <div class="message success">
        {message}
      </div>
    </div>
  {/if}
  </main>
</div>

<style>
  main {
    margin: 0 auto;
    max-width: 500px;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    background-color: #2a2a2a;
  }

  h1 {
    text-align: center;
    margin-bottom: 0.5rem;
  }

  .description {
    text-align: center;
    color: #aaa;
    margin-bottom: 2rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
    position: relative;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #333;
    color: #fff;
  }

  .hint {
    position: absolute;
    right: 0;
    top: 0;
    font-size: 0.8rem;
    color: #aaa;
  }

  button {
    width: 100%;
    padding: 0.75rem;
    background-color: #4a56e2;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  button:hover:not(:disabled) {
    background-color: #3a46d2;
  }

  button:disabled {
    background-color: #666;
    cursor: not-allowed;
  }

  .message {
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 4px;
    color: white;
    text-align: center;
  }

  .success {
    background-color: #2e7d32;
  }

  .error {
    background-color: #c62828;
  }

  .results {
    margin-top: 2rem;
    padding: 1rem;
    border-radius: 4px;
    background-color: #333;
  }

  .results h2 {
    text-align: center;
    margin-bottom: 1rem;
    font-size: 1.2rem;
  }

  .stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stat-item {
    background-color: #3a3a3a;
    padding: 1rem;
    border-radius: 4px;
    text-align: center;
  }

  .stat-label {
    display: block;
    margin-bottom: 0.5rem;
    color: #aaa;
    font-size: 0.9rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
  }
</style>
