import React, { useState, useCallback, useEffect } from 'react';

import { RadioButtonGroup, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GSelect from 'containers/GSelect/GSelect';
import { useStore } from 'state/useStore';

import styles from './EscalationVariants.module.css';

const cx = cn.bind(styles);

interface EscalationVariantsProps {}

// interface AssignRespondersPickerProps {
//   value: any;
//   handleAddResponders: (id) => void;
//   respondersOption: string;
// }

// const AssignRespondersPicker = (props: AssignRespondersPickerProps) => {
//   const { value = { searchTerm: '' }, handleAddResponders, respondersOption } = props;
//   const store = useStore();
//   console.log('respondersOption', respondersOption);

//   const onSearchTermChangeCallback = useCallback(
//     (e: ChangeEvent<HTMLInputElement>) => {
//       const filters = {
//         ...value,
//         searchTerm: e.currentTarget.value,
//       };

//       if (respondersOption == 'schedules') {
//         store.scheduleStore.updateItems(filters);
//       }
//       if (respondersOption == 'users') {
//         store.userStore.updateItems(filters);
//       }
//     },
//     [value]
//   );
//     //   const respondersList = currentStore.getSearchResult();
//     if (respondersOption == 'schedules') {
//       const scheculesList = store.scheduleStore.getSearchResult();
//     }
//     if (respondersOption == 'users') {
//       const usersList = store.userStore.getSearchResult();
//     }

//   return (
//     <div className={cx('assign-responders-picker')}>
//       <Input
//         prefix={<Icon name="search" />}
//         className={cx('search', 'control')}
//         placeholder="Search"
//         value={value.searchTerm}
//         onChange={onSearchTermChangeCallback}
//       />
//       <div className={cx('assign-responders-list')}>
//         {respondersOption == 'schedules'
//           ? store.scheduleStore.getSearchResult()?.map((schedule) => (
//               <div
//                 key={schedule.id}
//                 className={cx('assign-responders-item')}
//                 onClick={() => handleAddResponders(schedule)}
//               >
//                 {schedule.name}
//               </div>
//             ))
//           : store.userStore.getSearchResult()?.map((user) => (
//               <div key={user.pk} className={cx('assign-responders-item')} onClick={() => handleAddResponders(user)}>
//                 {user.name}
//               </div>
//             ))}
//       </div>
//     </div>
//   );
// };

const EscalationVariants = observer(({}: EscalationVariantsProps) => {
  const store = useStore();
  const [activeOption, setActiveOption] = useState('schedules');
  const [showEscalationVariants, setShowEscalationVariants] = useState(false);
  const [responders, setResponders] = useState([]);
  const [schedulesIds, setSchedulesIds] = useState([]);
  const [usersIds, setUsersIds] = useState([]);

  useEffect(() => {
    store.scheduleStore.updateItems('');
  }, []);

  const handleOpenEscalationVariants = (status) => {
    if (status) {
      setShowEscalationVariants(false);
    } else {
      setShowEscalationVariants(true);
    }
  };

  const handleOptionChange = useCallback((option: string) => {
    console.log('OPTION', option);
    setActiveOption(option);
  }, []);

  const addUserResponders = (value, items) => {
    console.log('ITEMS', items);
    usersIds.push(value);
    setUsersIds(usersIds);
    responders.push(...items);
    setResponders(responders);
  };

  const addSchedulesResponders = (value, items) => {
    console.log('ITEMS', items);
    schedulesIds.push(value);
    setSchedulesIds(schedulesIds);
    responders.push(...items);
    setResponders(responders);
  };

  return (
    <>
      <div>
        {responders.map((responder) => (
          <div key={responder.id || responder.pk}>{responder.name || responder.username}</div>
        ))}
        <div className={cx('assign-responders-button')}>
          <Button variant="secondary">Add responders</Button>
          <Button
            variant="secondary"
            onClick={() => handleOpenEscalationVariants(showEscalationVariants)}
            icon="angle-down"
            style={{ width: '24px' }}
          ></Button>
        </div>
        {/* {showEscalationVariants && <EscalationVariants onHide={() => setShowEscalationVariants(false)} />} */}
        {showEscalationVariants && (
          <div className={cx('escalation-variants-dropdown')}>
            <RadioButtonGroup
              options={[
                { value: 'schedules', label: 'Schedules' },
                { value: 'users', label: 'Users' },
              ]}
              value={activeOption}
              onChange={handleOptionChange}
              fullWidth
            />
            {/* <AssignRespondersPicker value handleAddResponders={addResponders} respondersOption={activeOption} /> */}
            {activeOption === 'schedules' && (
              <GSelect
                isMulti
                modelName="scheduleStore"
                displayField="name"
                valueField="id"
                placeholder="Select Schedules"
                className={cx('select', 'control')}
                value={schedulesIds}
                onChange={addSchedulesResponders}
                fromOrganization
              />
            )}

            {activeOption === 'users' && (
              <GSelect
                isMulti
                showSearch
                allowClear
                modelName="userStore"
                displayField="username"
                valueField="pk"
                placeholder="Select Users"
                className={cx('select', 'control', 'multiSelect')}
                value={usersIds}
                onChange={addUserResponders}
              />
            )}
          </div>
        )}
      </div>
    </>
  );
});

export default EscalationVariants;
