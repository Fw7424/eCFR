function toggle(id, btn) {
    const content = document.getElementById(id);
    const isOpen = content.style.display === 'block';
    content.style.display = isOpen ? 'none' : 'block';
    if (btn) btn.classList.toggle('open', !isOpen);
}