async function fetchData() {
    const res = await fetch('/data');
    const data = await res.json();

    if (document.getElementById("in")) {
        document.getElementById("in").innerText = data.in;
        document.getElementById("out").innerText = data.out;
        document.getElementById("total").innerText = data.in + data.out;
    }
}

setInterval(fetchData, 1000);