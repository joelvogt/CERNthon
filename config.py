client_id = 'osx_client'
modules = dict(
    remote_file=dict(
        buffer_size=8192,
        connection = 'tcpsock',
        serialization = dict(
            data='python_pickling',
            results='python_pickling'
        )
    ),
    basic_operations=dict(
        buffer_size=8192,
        connection='tcpsock',
        serialization=dict(
            data='python_pickling',
            results='python_pickling'
    )
    )
)