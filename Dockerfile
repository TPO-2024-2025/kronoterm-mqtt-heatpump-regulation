FROM homeassistant/home-assistant:2025.2.4

ADD ./custom_components/kronoterm_integration /config/custom_components/kronoterm_integration
ADD ./config/configuration.yaml /config/configuration.yaml
ADD ./config/automations.yaml /config/automations.yaml

CMD /init