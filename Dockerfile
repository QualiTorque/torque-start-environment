FROM qtorque/torque-cli:1.8

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]