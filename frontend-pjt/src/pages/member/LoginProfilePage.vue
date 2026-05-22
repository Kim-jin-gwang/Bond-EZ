<script setup>
defineProps({
  isLoggedIn: {
    type: Boolean,
    default: false,
  },
  user: {
    type: Object,
    default: () => ({}),
  },
})

defineEmits(['login', 'logout'])
</script>

<template>
  <section class="page profile-page">
    <!-- 로그인 패널 -->
    <section v-if="!isLoggedIn" class="login-panel">
      <div class="login-header">
        <span class="brand-mark">易</span>
        <h1>채권이지 시작하기</h1>
        <p>나에게 딱 맞는 채권 투자 정보를 확인하세요.</p>
      </div>
      <div class="social-buttons">
        <button class="social kakao" type="button" @click="$emit('login')">
          <span class="icon">●</span> 카카오로 시작하기
        </button>
        <button class="social naver" type="button" @click="$emit('login')">
          <span class="icon">●</span> 네이버로 시작하기
        </button>
        <button class="social google" type="button" @click="$emit('login')">
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
              <span class="badge">{{ user.type }}</span>
            </div>
            <p class="email">{{ user.email }}</p>
          </div>
        </div>
        <button class="btn-edit" type="button">프로필 수정</button>
      </header>

      <!-- 투자 요약 정보 -->
      <div class="summary-grid">
        <div class="summary-card">
          <span class="label">관심 채권</span>
          <span class="value">12<small>개</small></span>
        </div>
        <div class="summary-card">
          <span class="label">알림 설정</span>
          <span class="value active">ON</span>
        </div>
        <div class="summary-card">
          <span class="label">최근 조회</span>
          <span class="value">5<small>건</small></span>
        </div>
      </div>

      <!-- 상세 설정 섹션 -->
      <div class="settings-group">
        <h2>내 투자 관리</h2>
        <div class="settings-list">
          <button type="button" class="list-item">
            <div class="item-content">
              <strong>관심 채권 관리</strong>
              <span>저장한 채권의 시세 변화를 확인하세요</span>
            </div>
            <span class="arrow">→</span>
          </button>
          <button type="button" class="list-item">
            <div class="item-content">
              <strong>투자 성향 진단</strong>
              <span>현재 설정: {{ user.type }} (재진단 가능)</span>
            </div>
            <span class="arrow">→</span>
          </button>
          <button type="button" class="list-item">
            <div class="item-content">
              <strong>CALL 일정 알림</strong>
              <span>발행사 옵션 행사 공시를 빠르게 알려드립니다</span>
            </div>
            <span class="toggle">ON</span>
          </button>
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
        <button class="btn-logout" type="button" @click="$emit('logout')">로그아웃</button>
        <button class="btn-withdraw" type="button">회원탈퇴</button>
      </footer>
    </section>
  </section>
</template>
