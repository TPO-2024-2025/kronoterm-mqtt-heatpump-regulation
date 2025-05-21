FROM homeassistant/home-assistant:2025.2.4

ADD ./src/custom_components/kronoterm_integration /config/custom_components/kronoterm_integration
ADD ./src/config/configuration.yaml /config/configuration.yaml
ADD ./src/config/automations.yaml /config/automations.yaml

CMD /init