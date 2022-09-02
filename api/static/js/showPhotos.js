function deletePhoto(filename) {
    const url = window.location['origin']+"/"+"deletePhoto/"+filename;
    fetch(url, { method: 'DELETE' })
    .then((resp) => {
        console.log(resp)
        console.log("deleted file with success")
    }).catch((error) => {
        console.log("something wrong. error below:")
        console.log(error)
    })
    window.location.reload()
}