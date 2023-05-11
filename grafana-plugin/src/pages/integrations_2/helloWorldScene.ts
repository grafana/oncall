import { EmbeddedScene, SceneFlexLayout, SceneFlexItem, VizPanel } from '@grafana/scenes';

export function getScene() {
  return new EmbeddedScene({
    body: new SceneFlexLayout({
      children: [
        new SceneFlexItem({
          width: '50%',
          height: 300,
          body: new VizPanel({
            title: 'Hello world panel',
            pluginId: 'text',
            options: {
              content: 'Hello world! ',
            },
          }),
        }),
      ],
    }),
  });
}
