document.addEventListener('DOMContentLoaded', function() {
    const navbarCollapse = document.getElementById('navbarNav');
    const aboutUsLink = document.querySelector('[data-bs-target="#aboutUsModal"]');
    const aboutUsModal = document.getElementById('aboutUsModal');
    
    // 当点击 About Us 链接时收起导航栏
    if (aboutUsLink) {
        aboutUsLink.addEventListener('click', function() {
            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
            if (bsCollapse) {
                bsCollapse.hide();
            }
        });
    }
    
    // 监听模态框关闭事件
    if (aboutUsModal) {
        aboutUsModal.addEventListener('hidden.bs.modal', function () {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // 阻止 Bootstrap 创建 modal-backdrop
        const modalInstance = new bootstrap.Modal(aboutUsModal, {
            backdrop: false
        });
    }
}); 