let checkouts = document.querySelectorAll('.checkout_item_wrapper')

checkouts.forEach((e) => {
    e.addEventListener('click', () => {
        e.classList.toggle('hidden')
        checkouts.forEach((a) => {
            if (a != e) {
                a.classList.add('hidden')
            }
        })
    })
})