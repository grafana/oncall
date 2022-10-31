import { capitalCase } from 'change-case';

export function getLabelFromTemplateName(templateName: string, group: any) {
  let arrayFromName = capitalCase(templateName).split(' ', 4);
  let arrayWithNeededValues;
  if (group === 'alert behaviour') {
    arrayWithNeededValues = arrayFromName.slice(0, arrayFromName.lastIndexOf('Template'));
  } else {
    arrayWithNeededValues = arrayFromName.slice(1, arrayFromName.lastIndexOf('Template'));
  }
  return arrayWithNeededValues.join(' ');
}
