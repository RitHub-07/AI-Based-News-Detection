document.addEventListener('DOMContentLoaded', function () {
    const contactForm = document.getElementById('contact-form');
    const formStatus = document.getElementById('form-status');
    const btnText = document.getElementById('btn-text');
    const submitBtn = document.getElementById('submit-btn');
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.scroll-section');
    const charCount = document.querySelector('.char-count');
    const newsText = document.querySelector('textarea[name="news_text"]');

    function setStatus(type, message) {
        if (!formStatus) return;
        formStatus.className = `form-status ${type}`;
        formStatus.textContent = message;
        formStatus.style.display = 'block';
    }

    if (newsText && charCount) {
        const updateCount = () => {
            charCount.textContent = `${newsText.value.length} characters`;
        };
        newsText.addEventListener('input', updateCount);
        updateCount();
    }

    if (contactForm) {
        contactForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const name = document.getElementById('name')?.value.trim() || '';
            const email = document.getElementById('email')?.value.trim() || '';
            const message = document.getElementById('message')?.value.trim() || '';

            if (!name || !email || !message) {
                setStatus('error', 'All fields are required.');
                return;
            }

            if (!email.includes('@') || !email.includes('.')) {
                setStatus('error', 'Please enter a valid email address.');
                return;
            }

            if (!submitBtn || !btnText) return;

            submitBtn.disabled = true;
            btnText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            setStatus('info', 'Sending message...');

            const formData = new FormData(contactForm);

            try {
                const response = await fetch(contactForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'Accept': 'application/json' }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                contactForm.reset();
                setStatus('success', '✅ Message sent successfully!');
                btnText.textContent = 'Message Sent!';

                if (charCount && newsText) {
                    charCount.textContent = `${newsText.value.length} characters`;
                }

                setTimeout(() => {
                    btnText.textContent = 'Send Message';
                    submitBtn.disabled = false;
                    if (formStatus) {
                        formStatus.style.display = 'none';
                    }
                }, 4000);
            } catch (error) {
                setStatus('error', '❌ Oops! Please check your connection.');
                btnText.textContent = 'Try Again';
                submitBtn.disabled = false;
            }
        });
    }

    function updateActiveNav() {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (window.scrollY >= sectionTop - 180) {
                current = section.getAttribute('id');
            }
        });

        navItems.forEach(item => {
            item.classList.remove('active');
            const href = item.getAttribute('href') || '';
            if (current && href.includes(`#${current}`)) {
                item.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav);
    updateActiveNav();
});