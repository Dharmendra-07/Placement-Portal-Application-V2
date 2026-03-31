<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Browse Placement Drives</h5>

    <!-- Search & filter bar -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-body py-3">
        <div class="row g-2 align-items-end">
          <div class="col-md-3">
            <label class="form-label small fw-medium">Job title / keyword</label>
            <input v-model="filters.q" type="text" class="form-control form-control-sm"
                   placeholder="Software Engineer, Data..." @input="fetchDrives" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Company</label>
            <input v-model="filters.company" type="text"
                   class="form-control form-control-sm"
                   placeholder="Company name..." @input="fetchDrives" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Skills</label>
            <input v-model="filters.skills" type="text"
                   class="form-control form-control-sm"
                   placeholder="Python, React..." @input="fetchDrives" />
          </div>
          <div class="col-md-2">
            <div class="form-check mt-3">
              <input class="form-check-input" type="checkbox"
                     id="eligibleOnly" v-model="filters.eligible_only"
                     @change="fetchDrives" />
              <label class="form-check-label small" for="eligibleOnly">
                Eligible only
              </label>
            </div>
          </div>
          <div class="col-md-1">
            <button class="btn btn-sm btn-outline-secondary w-100"
                    @click="resetFilters">Reset</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Results count -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <span class="text-muted small">{{ drives.length }} drives found</span>
      <div class="d-flex gap-2">
        <button class="btn btn-sm"
                :class="viewMode === 'card' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="viewMode = 'card'">Cards</button>
        <button class="btn btn-sm"
                :class="viewMode === 'table' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="viewMode = 'table'">Table</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="drives.length === 0"
         class="text-muted text-center py-5">
      No drives match your search.
    </div>

    <!-- Card view -->
    <div v-else-if="viewMode === 'card'" class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="d in drives" :key="d.id">
        <div class="card border-0 shadow-sm h-100"
             :class="{ 'border-start border-3 border-success': d.eligible,
                       'border-start border-3 border-warning': !d.eligible }">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-1">
              <h6 class="fw-bold mb-0">{{ d.job_title }}</h6>
              <span class="badge"
                    :class="d.eligible ? 'bg-success' : 'bg-warning text-dark'">
                {{ d.eligible ? 'Eligible' : 'Not eligible' }}
              </span>
            </div>
            <p class="text-primary small fw-medium mb-2">{{ d.company_name }}</p>
            <p class="text-muted small mb-2"
               style="display:-webkit-box;-webkit-line-clamp:2;
                      -webkit-box-orient:vertical;overflow:hidden">
              {{ d.job_description || 'No description provided.' }}
            </p>
            <div class="row g-1 small text-muted mb-2">
              <div class="col-6">
                Salary: {{ d.salary_min ? `₹${d.salary_min}–${d.salary_max} LPA` : '—' }}
              </div>
              <div class="col-6">Location: {{ d.location || 'Remote' }}</div>
              <div class="col-6">Min CGPA: {{ d.min_cgpa }}</div>
              <div class="col-6">Deadline: {{ formatDate(d.application_deadline) }}</div>
            </div>

            <!-- Skills chips -->
            <div v-if="d.skills_required" class="d-flex flex-wrap gap-1 mb-2">
              <span v-for="sk in d.skills_required.split(',')" :key="sk"
                    class="badge bg-light text-secondary border">
                {{ sk.trim() }}
              </span>
            </div>

            <div v-if="!d.eligible"
                 class="alert alert-warning py-1 px-2 small mb-0 mt-1">
              {{ d.eligibility_note }}
            </div>
          </div>
          <div class="card-footer bg-transparent">
            <button v-if="d.already_applied"
                    class="btn btn-sm btn-secondary w-100" disabled>
                Applied ✓
            </button>
            <button v-else-if="d.eligible"
                    class="btn btn-sm btn-primary w-100"
                    :disabled="applying === d.id"
                    @click="apply(d.id)">
              <span v-if="applying === d.id"
                    class="spinner-border spinner-border-sm me-1"></span>
              Apply Now
            </button>
            <button v-else
                    class="btn btn-sm btn-outline-secondary w-100" disabled>
              Not Eligible
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Table view -->
    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Job Title</th>
            <th>Company</th>
            <th>Salary</th>
            <th>Min CGPA</th>
            <th>Deadline</th>
            <th>Eligible</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>
              <div class="fw-medium">{{ d.job_title }}</div>
              <div class="text-muted small">{{ d.job_type }}</div>
            </td>
            <td class="small">{{ d.company_name }}</td>
            <td class="small">
              {{ d.salary_min ? `₹${d.salary_min}–${d.salary_max} LPA` : '—' }}
            </td>
            <td class="small">{{ d.min_cgpa }}</td>
            <td class="small">{{ formatDate(d.application_deadline) }}</td>
            <td>
              <span class="badge"
                    :class="d.eligible ? 'bg-success' : 'bg-warning text-dark'">
                {{ d.eligible ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>
              <button v-if="d.already_applied"
                      class="btn btn-sm btn-secondary" disabled>
                Applied
              </button>
              <button v-else-if="d.eligible"
                      class="btn btn-sm btn-primary"
                      :disabled="applying === d.id"
                      @click="apply(d.id)">
                Apply
              </button>
              <span v-else class="text-muted small">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentDrivesView',
  data() {
    return {
      drives: [], loading: true, applying: null,
      viewMode: 'card',
      filters: { q: '', company: '', skills: '', eligible_only: false },
    }
  },
  created() { this.fetchDrives() },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const { data } = await api.get('/student/drives', {
          params: {
            q:             this.filters.q,
            company:       this.filters.company,
            skills:        this.filters.skills,
            eligible_only: this.filters.eligible_only,
          }
        })
        this.drives = data
      } finally { this.loading = false }
    },
    resetFilters() {
      this.filters = { q: '', company: '', skills: '', eligible_only: false }
      this.fetchDrives()
    },
    async apply(driveId) {
      this.applying = driveId
      try {
        await api.post(`/student/drives/${driveId}/apply`)
        const d = this.drives.find(x => x.id === driveId)
        if (d) d.already_applied = true
      } catch (err) {
        alert(err.response?.data?.message || 'Application failed.')
      } finally { this.applying = null }
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
  },
}
</script>
