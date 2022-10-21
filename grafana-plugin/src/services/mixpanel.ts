const mixpanel = window.mixpanel;

const actions = {
  identify: (id: any) => {
    if (mixpanel) {
      mixpanel.identify(id);
    }
  },
  alias: (id: any) => {
    if (mixpanel) {
      mixpanel.alias(id);
    }
  },
  track: (name: any, props: any) => {
    if (mixpanel) {
      mixpanel.track(name, props);
    }
  },
  people: {
    set: (props: any) => {
      if (mixpanel) {
        mixpanel.people.set(props);
      }
    },
  },
};

export const Mixpanel = actions;
