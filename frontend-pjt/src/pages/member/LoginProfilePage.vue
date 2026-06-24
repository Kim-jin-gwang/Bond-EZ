<script setup>
import { ref, watch } from 'vue'
import { useAppStore } from '../../stores/app'
import { signupApi, updateMeApi } from '../../api/auth'

const props = defineProps({
  isLoggedIn: {
    type: Boolean,
    default: false,
  },
  user: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['login', 'logout', 'navigate'])

const appStore = useAppStore()

const isRedirecting = ref(false)
const showAllFavorites = ref(false)
const showAllRecent = ref(false)

// Profile Edit Modal States
const editProfileOpen = ref(false)
const editEmail = ref(props.user?.email || '')
const editPassword = ref('')
const editPasswordConfirm = ref('')
const profileError = ref('')
const profileSuccess = ref('')
const isSaving = ref(false)

watch(() => props.user, (u) => {
  if (u) {
    editEmail.value = u.email || ''
  }
}, { immediate: true })

async function handleUpdateProfile() {
  profileError.value = ''
  profileSuccess.value = ''

  if (editPassword.value && editPassword.value !== editPasswordConfirm.value) {
    profileError.value = '새 비밀번호와 비밀번호 확인이 일치하지 않습니다.'
    return
  }

  isSaving.value = true
  try {
    const payload = {
      email: editEmail.value.trim(),
    }
    if (editPassword.value) {
      payload.password = editPassword.value
      payload.password_confirm = editPasswordConfirm.value
    }
    await updateMeApi(payload)
    profileSuccess.value = '프로필 수정이 완료되었습니다.'
    
    if (appStore.user) {
      appStore.user.email = editEmail.value.trim()
    }
    
    editPassword.value = ''
    editPasswordConfirm.value = ''
    
    setTimeout(() => {
      editProfileOpen.value = false
      profileSuccess.value = ''
    }, 1500)
  } catch (err) {
    console.error('Update profile error:', err)
    profileError.value = err.payload?.message || err.message || '프로필 수정에 실패했습니다.'
  } finally {
    isSaving.value = false
  }
}

// 'login' or 'signup'
const activeTab = ref('login')

// Forms state
const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const firstName = ref('')
const lastName = ref('')

const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!username.value.trim() || !password.value) {
    errorMessage.value = '아이디 또는 이메일과 비밀번호를 입력해주세요.'
    return
  }

  isLoading.value = true
  try {
    isRedirecting.value = true
    await appStore.login({
      username: username.value.trim(),
      password: password.value,
    })
    // Reset forms
    username.value = ''
    password.value = ''
    emit('navigate', 'home')
  } catch (err) {
    isRedirecting.value = false
    console.error('Login error:', err)
    errorMessage.value = err.payload?.message || err.message || '로그인에 실패했습니다. 정보를 다시 확인해주세요.'
  } finally {
    isLoading.value = false
  }
}

async function handleSignup() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!username.value.trim() || !email.value.trim() || !password.value || !passwordConfirm.value) {
    errorMessage.value = '필수 항목(* 표시)을 모두 입력해주세요.'
    return
  }

  if (password.value !== passwordConfirm.value) {
    errorMessage.value = '비밀번호와 비밀번호 확인이 일치하지 않습니다.'
    return
  }

  isLoading.value = true
  try {
    await signupApi({
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
      password_confirm: passwordConfirm.value,
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
    })
    successMessage.value = '회원가입이 완료되었습니다! 로그인해 주세요.'
    
    // Auto switch to login tab with the signed-up username pre-filled
    const signedUpUser = username.value.trim()
    activeTab.value = 'login'
    username.value = signedUpUser
    password.value = ''
    passwordConfirm.value = ''
  } catch (err) {
    console.error('Signup error:', err)
    errorMessage.value = err.payload?.message || err.message || '회원가입에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

async function handleLogout() {
  isLoading.value = true
  try {
    await appStore.logout()
  } catch (err) {
    console.error('Logout error:', err)
  } finally {
    isLoading.value = false
  }
}

async function handleWithdraw() {
  if (!confirm('정말로 탈퇴하시겠습니까? 관련 데이터가 모두 삭제됩니다.')) {
    return
  }
  
  isLoading.value = true
  try {
    await appStore.withdraw()
    alert('회원탈퇴가 완료되었습니다.')
    emit('navigate', 'home')
  } catch (err) {
    console.error('Withdraw error:', err)
    errorMessage.value = err.payload?.message || err.message || '회원탈퇴에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <section class="page profile-page">
    <!-- 로그인/회원가입 패널 -->
    <section v-if="!isLoggedIn || isRedirecting" class="login-panel">
      <div class="login-header">
        <span class="brand-mark">易</span>
        <h1>채권이지 시작하기</h1>
        <p>나에게 딱 맞는 채권 투자 정보를 확인하세요.</p>
      </div>

      <!-- 탭 스위처 -->
      <div class="auth-tabs">
        <button 
          type="button" 
          :class="{ active: activeTab === 'login' }" 
          @click="activeTab = 'login'; errorMessage = ''; successMessage = ''"
        >
          로그인
        </button>
        <button 
          type="button" 
          :class="{ active: activeTab === 'signup' }" 
          @click="activeTab = 'signup'; errorMessage = ''; successMessage = ''"
        >
          회원가입
        </button>
      </div>

      <!-- 에러/성공 메시지 알림 -->
      <div v-if="errorMessage" class="alert-box error" role="alert">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="alert-box success" role="alert">
        {{ successMessage }}
      </div>

      <!-- 로그인 폼 -->
      <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="auth-form">
        <div class="input-group">
          <label for="login-username">아이디 또는 이메일</label>
          <input 
            type="text" 
            id="login-username" 
            v-model="username" 
            placeholder="아이디 또는 이메일 입력" 
            required 
            :disabled="isLoading"
          />
        </div>
        <div class="input-group">
          <label for="login-password">비밀번호</label>
          <input 
            type="password" 
            id="login-password" 
            v-model="password" 
            placeholder="비밀번호 입력" 
            required 
            :disabled="isLoading"
          />
        </div>
        <button type="submit" class="btn-submit" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>로그인</span>
        </button>
      </form>

      <!-- 회원가입 폼 -->
      <form v-else @submit.prevent="handleSignup" class="auth-form">
        <div class="input-group">
          <label for="signup-username">아이디 *</label>
          <input 
            type="text" 
            id="signup-username" 
            v-model="username" 
            placeholder="아이디 입력" 
            required 
            :disabled="isLoading"
          />
        </div>
        <div class="input-group">
          <label for="signup-email">이메일 *</label>
          <input 
            type="email" 
            id="signup-email" 
            v-model="email" 
            placeholder="example@email.com" 
            required 
            :disabled="isLoading"
          />
        </div>
        <div class="form-row">
          <div class="input-group">
            <label for="signup-lastname">성</label>
            <input 
              type="text" 
              id="signup-lastname" 
              v-model="lastName" 
              placeholder="홍" 
              :disabled="isLoading"
            />
          </div>
          <div class="input-group">
            <label for="signup-firstname">이름</label>
            <input 
              type="text" 
              id="signup-firstname" 
              v-model="firstName" 
              placeholder="길동" 
              :disabled="isLoading"
            />
          </div>
        </div>
        <div class="input-group">
          <label for="signup-password">비밀번호 *</label>
          <input 
            type="password" 
            id="signup-password" 
            v-model="password" 
            placeholder="비밀번호 입력" 
            required 
            :disabled="isLoading"
          />
        </div>
        <div class="input-group">
          <label for="signup-confirm">비밀번호 확인 *</label>
          <input 
            type="password" 
            id="signup-confirm" 
            v-model="passwordConfirm" 
            placeholder="비밀번호 재입력" 
            required 
            :disabled="isLoading"
          />
        </div>
        <button type="submit" class="btn-submit" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>가입하기</span>
        </button>
      </form>

      <!-- 구분선 -->
      <div class="divider">
        <span>또는 간편로그인</span>
      </div>

      <!-- 소셜 로그인 영역 -->
      <div class="social-buttons">
        <button class="social kakao" type="button" :disabled="isLoading">
          <span class="icon">●</span> 카카오로 시작하기
        </button>
        <button class="social naver" type="button" :disabled="isLoading">
          <span class="icon">●</span> 네이버로 시작하기
        </button>
        <button class="social google" type="button" :disabled="isLoading">
          <span class="icon">G</span> 구글로 시작하기
        </button>
      </div>
      <p class="disclaimer">투자 판단과 책임은 투자자 본인에게 있습니다.</p>
    </section>

    <!-- 전문적인 마이페이지 -->
    <section v-else class="my-page professional">
      <!-- 프로필 헤더 -->
      <header class="profile-header">
        <div class="profile-main">
          <div class="avatar-large">{{ user.avatar }}</div>
          <div class="info">
            <div class="name-tag">
              <h1>{{ user.name }} 님</h1>
            </div>
            <p class="email">{{ user.email }}</p>
          </div>
        </div>
        <button class="btn-edit" type="button" @click="editProfileOpen = true">프로필 수정</button>
      </header>

      <!-- 투자 요약 정보 -->
      <div class="summary-grid">
        <div class="summary-card">
          <span class="label">관심 채권</span>
          <span class="value">{{ appStore.favoriteBonds.length }}<small>개</small></span>
        </div>
        <div class="summary-card">
          <span class="label">최근 조회</span>
          <span class="value">{{ appStore.recentBonds.length }}<small>건</small></span>
        </div>
      </div>

      <!-- 상세 설정 섹션 -->
      <div class="settings-group">
        <div class="settings-group-header">
          <h2>내가 등록한 관심 채권</h2>
          <button 
            v-if="appStore.favoriteBonds.length > 2"
            type="button" 
            class="btn-view-more-header" 
            @click="showAllFavorites = !showAllFavorites"
          >
            {{ showAllFavorites ? '접기' : '전체보기 (' + appStore.favoriteBonds.length + '개)' }}
          </button>
        </div>
        <div v-if="appStore.favoriteBonds.length === 0" class="empty-favorites">
          <p>등록된 관심 채권이 없습니다.<br>채권 시세에서 관심 있는 채권을 추가해 보세요!</p>
          <button type="button" class="btn-goto-market" @click="emit('navigate', 'market')">
            채권 시세 보러가기
          </button>
        </div>
        <div v-else class="favorites-list">
          <div v-for="bond in (showAllFavorites ? appStore.favoriteBonds : appStore.favoriteBonds.slice(0, 2))" :key="bond.bondId" class="favorite-item">
            <div class="bond-info" @click="emit('navigate', 'detail', { bond })">
              <div class="bond-meta-tags">
                <span class="type-tag">{{ bond.type }}</span>
                <span class="rating-tag" :class="bond.ratingGroup">{{ bond.rating }}</span>
              </div>
              <strong class="bond-name">{{ bond.name }}</strong>
              <div class="bond-details">
                <span>표면금리: <strong class="highlight">{{ bond.coupon }}</strong></span>
                <span>만기일: <strong>{{ bond.maturity }}</strong></span>
                <span>이자주기: <strong>{{ bond.interestCycle }}</strong></span>
              </div>
            </div>
            <button class="btn-remove-fav" type="button" @click="appStore.toggleFavorite(bond.bondId)" title="관심 채권 해제">
              ★
            </button>
          </div>

        </div>
      </div>

      <!-- 최근 조회 채권 섹션 -->
      <div class="settings-group">
        <div class="settings-group-header">
          <h2>최근 조회한 채권</h2>
          <button 
            v-if="appStore.recentBonds.length > 2"
            type="button" 
            class="btn-view-more-header" 
            @click="showAllRecent = !showAllRecent"
          >
            {{ showAllRecent ? '접기' : '전체보기 (' + appStore.recentBonds.length + '개)' }}
          </button>
        </div>
        <div v-if="appStore.recentBonds.length === 0" class="empty-favorites">
          <p>최근 조회한 채권이 없습니다.<br>채권 시세에서 채권 상세정보를 조회해 보세요!</p>
        </div>
        <div v-else class="favorites-list">
          <div v-for="bond in (showAllRecent ? appStore.recentBonds : appStore.recentBonds.slice(0, 2))" :key="bond.bondId" class="favorite-item">
            <div class="bond-info" @click="emit('navigate', 'detail', { bond })">
              <div class="bond-meta-tags">
                <span class="type-tag">{{ bond.type }}</span>
                <span class="rating-tag" :class="bond.ratingGroup">{{ bond.rating }}</span>
              </div>
              <strong class="bond-name">{{ bond.name }}</strong>
              <div class="bond-details">
                <span>표면금리: <strong class="highlight">{{ bond.coupon }}</strong></span>
                <span>만기일: <strong>{{ bond.maturity }}</strong></span>
                <span>이자주기: <strong>{{ bond.interestCycle }}</strong></span>
              </div>
            </div>
            <!-- 즐겨찾기(별) 버튼 -->
            <button 
              class="btn-favorite-recent" 
              :class="{ active: appStore.isFavorite(bond.bondId) }"
              type="button" 
              @click.stop="appStore.toggleFavorite(bond.bondId)" 
              title="관심 채권 등록/해제"
            >
              {{ appStore.isFavorite(bond.bondId) ? '★' : '☆' }}
            </button>
          </div>

        </div>
      </div>
      <div class="settings-group">
        <h2>서비스 지원</h2>
        <div class="settings-list">
          <button type="button" class="list-item">
            <div class="item-content">
              <strong>약관 및 정책</strong>
            </div>
            <span class="arrow">→</span>
          </button>
          <button type="button" class="list-item">
            <div class="item-content">
              <strong>공지사항</strong>
            </div>
            <span class="arrow">→</span>
          </button>
        </div>
      </div>

      <!-- 로그아웃 및 탈퇴 -->
      <footer class="profile-footer">
        <button class="btn-logout" type="button" @click="handleLogout" :disabled="isLoading">
          <span v-if="isLoading">로그아웃 중...</span>
          <span v-else>로그아웃</span>
        </button>
        <button class="btn-withdraw" type="button" @click="handleWithdraw" :disabled="isLoading">회원탈퇴</button>
      </footer>
    </section>

    <!-- 프로필 수정 모달 -->
    <div v-if="editProfileOpen" class="modal-overlay" @click.self="editProfileOpen = false">
      <div class="modal-box">
        <h3>프로필 수정 (비밀번호 변경)</h3>
        <form @submit.prevent="handleUpdateProfile" class="auth-form">
          <div v-if="profileError" class="alert-box error" role="alert">
            {{ profileError }}
          </div>
          <div v-if="profileSuccess" class="alert-box success" role="alert">
            {{ profileSuccess }}
          </div>
          <div class="input-group">
            <label for="edit-email">이메일</label>
            <input 
              type="email" 
              id="edit-email" 
              v-model="editEmail" 
              required 
              :disabled="isSaving"
            />
          </div>
          <div class="input-group">
            <label for="edit-password">새 비밀번호 (변경할 경우만 입력)</label>
            <input 
              type="password" 
              id="edit-password" 
              v-model="editPassword" 
              placeholder="새 비밀번호 입력"
              :disabled="isSaving"
            />
          </div>
          <div class="input-group">
            <label for="edit-password-confirm">새 비밀번호 확인</label>
            <input 
              type="password" 
              id="edit-password-confirm" 
              v-model="editPasswordConfirm" 
              placeholder="비밀번호 재입력"
              :disabled="isSaving"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="editProfileOpen = false" :disabled="isSaving">
              취소
            </button>
            <button type="submit" class="btn-save" :disabled="isSaving">
              <span v-if="isSaving" class="spinner"></span>
              <span v-else>저장</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-tabs {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--line, #e2e8f0);
}

.auth-tabs button {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 600;
  color: var(--muted, #64748b);
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.auth-tabs button.active {
  color: var(--primary, #3b82f6);
  border-bottom: 2px solid var(--primary, #3b82f6);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .input-group {
  flex: 1;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #1e293b);
}

.input-group input {
  width: 100%;
  box-sizing: border-box;
}

.btn-submit {
  background: var(--primary, #3b82f6);
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 8px;
}

.btn-submit:hover {
  opacity: 0.9;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 24px 0;
  color: var(--muted, #64748b);
  font-size: 12px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--line, #e2e8f0);
}

.divider span {
  padding: 0 10px;
}

.alert-box {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-align: left;
  margin-bottom: 16px;
}

.alert-box.error {
  background-color: color-mix(in srgb, var(--danger) 12%, var(--surface));
  color: #ef4444;
  border: 1px solid #fee2e2;
}

.alert-box.success {
  background-color: color-mix(in srgb, var(--good) 12%, var(--surface));
  color: #22c55e;
  border: 1px solid #dcfce7;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-favorites {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: var(--surface-soft, #f8fafc);
  border: 1px dashed var(--line, #e2e8f0);
  border-radius: 8px;
  text-align: center;
  color: var(--muted, #64748b);
  gap: 12px;
}

.empty-favorites p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.btn-goto-market {
  background: var(--surface);
  border: 1px solid var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-goto-market:hover {
  background: var(--primary, #3b82f6);
  color: white;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.favorite-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--line, #e2e8f0);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
}

.favorite-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.bond-info {
  flex: 1;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.bond-meta-tags {
  display: flex;
  gap: 6px;
  align-items: center;
}

.type-tag, .rating-tag {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
}

.type-tag {
  color: var(--muted, #64748b);
  background: var(--surface-soft, #f8fafc);
}

.rating-tag.AAA { color: #1f5f9f; background: #ebf3fb; }
.rating-tag.AA { color: #127c57; background: #e7f6f0; }
.rating-tag.A { color: #d98c31; background: #fff7ec; }
.rating-tag.BBB { color: #b42318; background: #fef2f2; }

.bond-name {
  font-size: 15px;
  font-weight: 800;
  color: var(--text, #1e293b);
  line-height: 1.4;
}

.bond-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--muted, #64748b);
}

.bond-details strong {
  color: var(--text, #1e293b);
}

.bond-details strong.highlight {
  color: var(--primary, #3b82f6);
}

.btn-remove-fav {
  background: none;
  border: none;
  color: #fbbf24;
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  line-height: 1;
  transition: transform 0.2s ease, color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove-fav:hover {
  transform: scale(1.2);
  color: #f59e0b;
}

.btn-withdraw {
  background: color-mix(in srgb, var(--danger) 12%, var(--surface)) !important;
  color: #ef4444 !important;
  border: 1px solid #fee2e2 !important;
}

.btn-withdraw:hover {
  background: #ef4444 !important;
  color: white !important;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: var(--surface);
  padding: 28px;
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  text-align: left;
}

.modal-box h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text, #1e293b);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-cancel,
.btn-save {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background: var(--surface-soft, #f8fafc);
  border: 1px solid var(--line, #e2e8f0);
  color: var(--muted, #64748b);
}

.btn-cancel:hover {
  background: var(--line, #e2e8f0);
  color: var(--text, #1e293b);
}

.btn-save {
  background: var(--primary, #3b82f6);
  border: 1px solid var(--primary, #3b82f6);
  color: white;
}

.btn-save:hover {
  opacity: 0.9;
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Scoped summary-grid layout and centered design */
.profile-page :deep(.summary-grid) {
  display: grid;
  grid-template-columns: repeat(2, 1fr) !important;
  gap: 20px;
  margin-bottom: 36px;
}

.profile-page :deep(.summary-card) {
  background: var(--surface);
  padding: 24px 20px;
  border-radius: 12px;
  border: 1px solid var(--line, #e2e8f0);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  transition: all 0.25s ease;
}

.profile-page :deep(.summary-card:hover) {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
  border-color: rgba(59, 130, 246, 0.2);
}

.profile-page :deep(.summary-card .label) {
  font-size: 14px;
  color: var(--muted, #64748b);
  font-weight: 800;
}

.profile-page :deep(.summary-card .value) {
  font-size: 32px;
  font-weight: 900;
  color: var(--primary, #3b82f6);
}

.profile-page :deep(.summary-card .value small) {
  font-size: 16px;
  font-weight: 700;
  color: var(--muted, #64748b);
  margin-left: 4px;
}

/* 헤더 내 전체보기 / 접기 UI */
.settings-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.settings-group-header h2 {
  margin: 0;
}

.btn-view-more-header {
  background: var(--surface);
  border: 1px solid var(--line, #e2e8f0);
  color: var(--muted, #64748b);
  padding: 6px 14px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.btn-view-more-header:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
  background: var(--surface-soft);
}

/* Recent list bookmark button */
.btn-favorite-recent {
  background: none;
  border: none;
  color: #cbd5e1;
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  line-height: 1;
  transition: transform 0.2s ease, color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-favorite-recent:hover {
  transform: scale(1.2);
  color: #f59e0b;
}

.btn-favorite-recent.active {
  color: #fbbf24;
}
</style>
