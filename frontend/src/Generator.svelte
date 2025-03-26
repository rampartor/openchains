<script>
  import Nav from './Nav.svelte';
  import { fetchUserInfo } from './auth.js';
  import { onMount } from 'svelte';

  let userCount = 10;
  let existingUserCount = 0;
  let slipsGenerated = 0;
  let existingSlipsCount = 0;
  let slipsPerUser = 1;
  let message = '';
  let loading = false;
  let users = [];
  let error = null;
  let firstCircleStep = 6;
  let bonusPercentage = 5;
  let possibleFullChains = 0;
  let searchUserId = '';
  let foundUser = null;
  let showUsersList = false;

  onMount(async () => {
    // Verify user is logged in and is admin
    fetchUserInfo();
    calculatePossibleChains();
    await fetchStats();
  });

  async function fetchStats() {
    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator/stats', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        existingUserCount = data.user_count || 0;
        existingSlipsCount = data.slip_count || 0;
        slipsGenerated = existingSlipsCount;
      } else {
        console.error('Failed to fetch stats');
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  function calculatePossibleChains() {
    if (userCount >= firstCircleStep) {
      possibleFullChains = Math.floor(userCount / firstCircleStep);
    } else {
      possibleFullChains = 0;
    }
  }

  async function generateUsers() {
    loading = true;
    message = '';
    error = null;

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ user_count: userCount }),
      });

      const data = await response.json();

      if (response.ok) {
        message = `Successfully generated ${data.users_created} users`;
        users = data.users || [];
        calculatePossibleChains();
      } else {
        error = data.detail || 'Error generating users';

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

  async function generateSlips() {
    loading = true;
    message = '';
    error = null;

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator/slips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          min_amount: 10.00,
          max_amount: 5000.00,
          bonus_percentage: bonusPercentage,
          slips_per_user: slipsPerUser
        }),
      });

      const data = await response.json();

      if (response.ok) {
        slipsGenerated += data.slips_created;
        message = `Generated ${data.slips_created} slips. Total: ${slipsGenerated}`;
        users = data.users || users;
      } else {
        error = data.detail || 'Error generating slips';

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

  async function startRotation() {
    loading = true;
    message = '';
    error = null;

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator/rotate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        message = `Rotation completed. ${data.rotated_users || 0} users rotated`;
        users = data.users || users;
      } else {
        error = data.detail || 'Error performing rotation';

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

  async function cleanupData() {
    loading = true;
    message = '';
    error = null;

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/generator/cleanup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        message = `Database cleaned up. Removed ${data.users_removed || 0} users and ${data.slips_removed || 0} slips.`;
        users = [];
        await fetchStats();
      } else {
        error = data.detail || 'Error cleaning up data';

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

  function toggleUsersList() {
    showUsersList = !showUsersList;
  }

  function searchUser() {
    if (!searchUserId) return;

    const userId = parseInt(searchUserId, 10);
    foundUser = users.find(user => user.id === userId);

    if (!foundUser) {
      error = `User with ID ${userId} not found`;
    } else {
      error = null;
    }
  }
</script>

<div>
  <Nav />
  <main>
    <h1>Chain Generator</h1>
    <p class="description">Test algorithm for random number generation in selected ranges</p>

    <div class="stats-panel">
      <div class="stats-item">
        <div class="stats-label">Existing Users</div>
        <div class="stats-value">{existingUserCount}</div>
      </div>
      <div class="stats-item">
        <div class="stats-label">Existing Slips</div>
        <div class="stats-value">{existingSlipsCount}</div>
      </div>
      <button on:click={cleanupData}
              disabled={loading || (existingUserCount === 0 && existingSlipsCount === 0)}
              class="action-button cleanup-button">
        Clean Database
      </button>
    </div>

    <div class="generator-panel">
      <div class="form-group">
        <label for="userCount">Number of users to generate:</label>
        <input
          id="userCount"
          type="number"
          bind:value={userCount}
          min="1"
          max="10000"
          on:input={calculatePossibleChains}
          required
        />
        <button on:click={generateUsers} disabled={loading} class="action-button">
          {loading ? 'Generating...' : 'Generate Users'}
        </button>
      </div>

      <div class="form-group">
        <button on:click={generateSlips} disabled={loading || existingUserCount === 0} class="action-button">
          Generate slips for each user
        </button>
        <div class="info-text">Slip amount range: 10.00₽ to 5,000.00₽</div>
        <div class="info-text">Each slip generates {bonusPercentage}% points which are transferred up the chain</div>
      </div>

      <div class="auto-fields">
        <div class="form-group">
          <div class="readonly-label" id="first-circle-label">First circle step:</div>
          <div class="readonly-value" aria-labelledby="first-circle-label">{firstCircleStep} followers</div>
          <div class="info-text">Bonus = {bonusPercentage}% of slip amount</div>
        </div>

        <div class="form-group">
          <div class="readonly-label" id="chains-label">Possible full chains:</div>
          <div class="readonly-value" aria-labelledby="chains-label">{possibleFullChains}</div>
          <div class="info-text">Based on user count and first circle step</div>
        </div>
      </div>

      <div class="form-group">
        <button on:click={startRotation}
                disabled={loading || existingUserCount === 0}
                class="action-button rotation-button">
          Enable Rotation!
        </button>
        <div class="info-text">
          When rotation ranges are enabled, a node automatically moves to the chain area
          that corresponds to the range based on the average amount of points transferred
          to predecessors at the time of rotation.
        </div>
      </div>

      <div class="form-group">
        <button on:click={toggleUsersList} class="action-button list-button">
          {showUsersList ? 'Hide' : 'Show'} Users List
        </button>
      </div>

      {#if showUsersList}
        <div class="users-section">
          <div class="search-user">
            <input
              type="number"
              placeholder="Enter user ID"
              bind:value={searchUserId}
              id="search-user-id"
              aria-label="Search user by ID"
            />
            <button on:click={searchUser} class="search-button">Find</button>
          </div>

          {#if foundUser}
            <div class="user-detail">
              <h3>User #{foundUser.id}</h3>
              <div class="user-stats">
                <div>Total slips amount: {foundUser.total_slips || 0}₽</div>
                <div>Total transferred bonus: {foundUser.total_bonus || 0}₽</div>
                <div>Total received bonus: {foundUser.received_bonus || 0}₽</div>
              </div>
            </div>
          {/if}

          <div class="users-table">
            <table>
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Slips Amount</th>
                  <th>Transferred Bonus</th>
                  <th>Received Bonus</th>
                </tr>
              </thead>
              <tbody>
                {#each users as user}
                  <tr>
                    <td>{user.id}</td>
                    <td>{user.total_slips || 0}₽</td>
                    <td>{user.total_bonus || 0}₽</td>
                    <td>{user.received_bonus || 0}₽</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    </div>

    {#if error}
      <div class="message error">
        {error}
      </div>
    {/if}

    {#if message}
      <div class="message success">
        {message}
      </div>
    {/if}
  </main>
</div>

<style>
  main {
    margin: 0 auto;
    max-width: 900px;
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

  .generator-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .form-group {
    margin-bottom: 0.5rem;
    position: relative;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .readonly-label {
    color: #aaa;
    font-size: 0.9rem;
  }

  .readonly-value {
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
  }

  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #333;
    color: #fff;
    margin-bottom: 0.5rem;
  }

  .action-button {
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

  .rotation-button {
    background-color: #e24a4a;
  }

  .rotation-button:hover:not(:disabled) {
    background-color: #d23a3a;
  }

  .list-button {
    background-color: #4ae29b;
    color: #222;
  }

  .list-button:hover:not(:disabled) {
    background-color: #3ad28b;
  }

  .action-button:hover:not(:disabled) {
    background-color: #3a46d2;
  }

  .action-button:disabled {
    background-color: #666;
    cursor: not-allowed;
  }

  .info-text {
    font-size: 0.85rem;
    color: #aaa;
    margin-top: 0.5rem;
  }

  .stats-panel {
    display: grid;
    grid-template-columns: 1fr 1fr 2fr;
    gap: 1rem;
    margin-bottom: 2rem;
    background-color: #333;
    padding: 1rem;
    border-radius: 4px;
  }

  .stats-item {
    text-align: center;
    background-color: #3a3a3a;
    padding: 0.75rem;
    border-radius: 4px;
  }

  .stats-label {
    font-size: 0.9rem;
    color: #aaa;
    margin-bottom: 0.4rem;
  }

  .stats-value {
    font-size: 1.8rem;
    font-weight: bold;
  }

  .cleanup-button {
    background-color: #e26c4a;
    align-self: center;
  }

  .cleanup-button:hover:not(:disabled) {
    background-color: #d25a3a;
  }

  .auto-fields {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    padding: 1rem;
    background-color: #333;
    border-radius: 4px;
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

  .users-section {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #333;
    border-radius: 4px;
  }

  .search-user {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .search-button {
    padding: 0.5rem 1rem;
    background-color: #4a56e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .user-detail {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background-color: #3a3a3a;
    border-radius: 4px;
  }

  .user-detail h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }

  .user-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.5rem;
  }

  .users-table {
    max-height: 400px;
    overflow-y: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #444;
  }

  th {
    background-color: #2a2a2a;
    position: sticky;
    top: 0;
  }

  tbody tr:hover {
    background-color: #3a3a3a;
  }
</style>
