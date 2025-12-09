def post_fork(server, worker):
    import app
    app.load_latest_model()
